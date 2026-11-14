"""Phase 2 v0 transfer engine.

This module is intentionally a structural retrieval layer, not a validator.  It
takes a typed operation contract, compares its declared behavior signature with
the seeded mechanism cards, and emits ``cent-transfer/1`` candidates.  A
candidate has no target artifact or target test; it remains ``candidate``.

Retrieval scores every production card and returns the top ``limit`` candidates.
``supported_operations`` is retained as a validation field, not as a retrieval
filter: it says whether a card has been reviewed for the operation, while the
behavior signature produces the ranked hypothesis set.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from .mechanisms import MECHANISM_BY_ID, MECHANISM_CARDS, MechanismCard
from .operation_contract import OperationContract, OperationTest
from .targets.glm import GLM_REFERENCE_TARGET
from .targets.glm_live import GLM_LIVE_TARGET
from .mapping import (
    MAPPING_OPERATORS,
    MappingOperator,
    OPERATOR_BY_ID as _OPERATOR_BY_ID,
)
from .transfer import (
    RELAXATION_CLASSES,
    MappingStep,
    RelaxationRecord,
    TargetProfile,
    TransferCandidate,
)

RESULT_SCHEMA = "cent-transfer-result/1"
DEFAULT_RETRIEVAL_LIMIT = 3


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


@dataclass(frozen=True)
class BehaviorSignature:
    """Declared behavior features used for structural retrieval."""

    primitive_chain: tuple[str, ...]
    stateful: bool
    feedback: bool
    conserved_quantities: tuple[str, ...]
    nonlinearity: str
    encoding: str
    precision: str

    def validate(self) -> None:
        _texts(self.primitive_chain, "behavior.primitive_chain")
        if not isinstance(self.stateful, bool):
            raise ValueError("behavior.stateful must be boolean")
        if not isinstance(self.feedback, bool):
            raise ValueError("behavior.feedback must be boolean")
        _texts(
            self.conserved_quantities,
            "behavior.conserved_quantities",
            allow_empty=True,
        )
        _text(self.nonlinearity, "behavior.nonlinearity")
        _text(self.encoding, "behavior.encoding")
        _text(self.precision, "behavior.precision")

    def as_dict(self) -> dict[str, Any]:
        return {
            "primitive_chain": list(self.primitive_chain),
            "stateful": self.stateful,
            "feedback": self.feedback,
            "conserved_quantities": list(self.conserved_quantities),
            "nonlinearity": self.nonlinearity,
            "encoding": self.encoding,
            "precision": self.precision,
        }


# ---------------------------------------------------------------------------
# Production operation contracts
# ---------------------------------------------------------------------------

SQRT = OperationContract(
    id="sqrt",
    name="square root",
    signature={
        "inputs": {"x": "nonnegative rational"},
        "outputs": {"root": "nonnegative rational or certified enclosure"},
    },
    semantics="root is the nonnegative value whose square is x.",
    reference={
        "kind": "exact-interval",
        "expression": "sqrt_q(x)",
        "path": "cent_compiler/interval.py",
    },
    tolerance="1/10000",
    tests=(
        OperationTest(
            id="sqrt-four",
            kind="exact",
            inputs={"x": "4"},
            expected="2",
            tolerance="0",
            provenance=("tests/test_core.py",),
            note="perfect square",
        ),
    ),
    target_constraints={
        "targets": ["glm-reference"],
        "target_validation": "reference-adapter-implemented; live not declared",
    },
    provenance=(
        "cent_compiler/interval.py",
        "cent_compiler/assembly.py",
        "tests/test_assembly.py",
    ),
    gaps=("no physical or measured target adapter; only the software reference route is certified",),
)

SUM = OperationContract(
    id="sum",
    name="exact sum",
    signature={
        "inputs": {"a": "rational", "b": "rational"},
        "outputs": {"total": "rational"},
    },
    semantics="total = a + b under a declared conservation junction (KCL or fluid).",
    reference={
        "kind": "exact-route",
        "expression": "a + b",
        "path": "cent_compiler/assembly.py",
    },
    tolerance="0",
    tests=(
        OperationTest(
            id="sum-five-sixths",
            kind="exact",
            inputs={"a": "1/2", "b": "1/3"},
            expected="5/6",
            tolerance="0",
            provenance=("tests/test_assembly.py",),
        ),
    ),
    target_constraints={
        "targets": ["glm-reference", "glm-live"],
        "target_validation": "reference-and-live-adapters-implemented",
    },
    provenance=("cent_compiler/assembly.py", "tests/test_assembly.py"),
    gaps=(
        "no physical junction measurement; reference and live KCL software adapters only",
        "the fluid route has a normalized-flow reference adapter only; no device binding or measured flow",
    ),
)

DIFFERENCE = OperationContract(
    id="difference",
    name="exact difference",
    signature={
        "inputs": {"a": "rational", "b": "rational"},
        "outputs": {"total": "rational"},
    },
    semantics="total = a - b under the declared KCL junction route.",
    reference={
        "kind": "exact-route",
        "expression": "a - b",
        "path": "cent_compiler/assembly.py",
    },
    tolerance="0",
    tests=(
        OperationTest(
            id="difference-one-sixth",
            kind="exact",
            inputs={"a": "1/2", "b": "1/3"},
            expected="1/6",
            tolerance="0",
            provenance=("tests/test_assembly.py",),
        ),
    ),
    target_constraints={
        "targets": ["glm-reference", "glm-live"],
        "target_validation": "reference-and-live-adapters-implemented",
    },
    provenance=("cent_compiler/assembly.py", "tests/test_assembly.py"),
    gaps=("no physical junction measurement; reference and live KCL software adapters only",),
)

QUANTIZED_CARRY = OperationContract(
    id="quantized_carry",
    name="quantized carry",
    signature={
        "inputs": {"x": "scalar in the declared range", "samples": "positive integer"},
        "outputs": {"code": "bounded sequence", "mean": "scalar estimate"},
    },
    semantics=(
        "Carry a scalar as a bounded code sequence whose declared mean "
        "reconstructs the input within the declared quantizer tolerance."
    ),
    reference={
        "kind": "exact-route",
        "description": "first-order error-feedback loop in cent_compiler/assembly.py",
        "path": "cent_compiler/assembly.py",
    },
    tolerance="1",
    tests=(
        OperationTest(
            id="quantized-half",
            kind="exact",
            inputs={"x": "1/2", "samples": "12"},
            expected="1/2",
            tolerance="0",
            provenance=("tests/test_assembly.py",),
            note="the declared 12-tick code mean is exactly one half",
        ),
    ),
    target_constraints={
        "targets": ["glm-reference"],
        "target_validation": "reference-adapter-implemented; live not declared",
    },
    provenance=(
        "cent_compiler/assembly.py",
        "cent_compiler/delta_sigma.py",
        "tests/test_assembly.py",
    ),
    gaps=("no live GLM carry adapter or measured hardware target; reference route only",),
)

MULT = OperationContract(
    id="mult",
    name="exact multiplication",
    signature={
        "inputs": {"a": "rational", "b": "rational"},
        "outputs": {"product": "rational"},
    },
    semantics="product = a * b under exact rational arithmetic.",
    reference={
        "kind": "exact-arithmetic",
        "expression": "mul(a, b)",
        "path": "cent_compiler/exact.py",
    },
    tolerance="0",
    tests=(
        OperationTest(
            id="mult-three-quarters-two-thirds",
            kind="exact",
            inputs={"a": "3/4", "b": "2/3"},
            expected="1/2",
            tolerance="0",
            provenance=("tests/test_transfer_contracts.py",),
        ),
    ),
    target_constraints={
        "targets": ["glm-reference"],
        "target_validation": (
            "log-domain-arithmetic reference adapter with fixed vectors; "
            "positive inputs only and a declared enclosure tolerance"
        ),
    },
    provenance=("cent_compiler/exact.py", "tests/test_transfer_contracts.py"),
    gaps=(
        "target evidence is a software reference enclosure with tolerance "
        "1/10000, not a measured junction",
    ),
)

DIV = OperationContract(
    id="div",
    name="exact division",
    signature={
        "inputs": {"numerator": "rational", "denominator": "nonzero rational"},
        "outputs": {"quotient": "rational"},
    },
    semantics="quotient = numerator / denominator under exact rational arithmetic; denominator is nonzero.",
    reference={
        "kind": "exact-arithmetic",
        "expression": "div(numerator, denominator)",
        "path": "cent_compiler/exact.py",
    },
    tolerance="0",
    tests=(
        OperationTest(
            id="div-half-three-quarters",
            kind="exact",
            inputs={"numerator": "1/2", "denominator": "3/4"},
            expected="2/3",
            tolerance="0",
            provenance=("tests/test_transfer_contracts.py",),
        ),
    ),
    target_constraints={
        "targets": ["glm-reference"],
        "target_validation": (
            "log-domain-arithmetic reference adapter with fixed vectors; "
            "positive inputs only and a declared enclosure tolerance"
        ),
    },
    provenance=("cent_compiler/exact.py", "tests/test_transfer_contracts.py"),
    gaps=(
        "target evidence is a software reference enclosure with tolerance "
        "1/10000, not a measured junction",
    ),
)

EXP = OperationContract(
    id="exp",
    name="exponential",
    signature={
        "inputs": {"x": "rational"},
        "outputs": {"value": "certified rational enclosure of exp(x)"},
    },
    semantics="value is a certified rational enclosure of e^x.",
    reference={
        "kind": "certified-interval",
        "expression": "exp_q(x)",
        "path": "cent_compiler/interval.py",
    },
    tolerance="1/10000",
    tests=(
        OperationTest(
            id="exp-zero",
            kind="exact",
            inputs={"x": "0"},
            expected="1",
            tolerance="0",
            provenance=("tests/test_core.py",),
        ),
    ),
    target_constraints={
        "targets": ["glm-reference"],
        "target_validation": (
            "log-domain-arithmetic reference adapter with fixed vectors; "
            "positive inputs only and a declared enclosure tolerance"
        ),
    },
    provenance=("cent_compiler/interval.py", "tests/test_core.py"),
    gaps=(
        "target evidence is a software reference enclosure with tolerance "
        "1/10000, not a measured junction",
    ),
)

LOG = OperationContract(
    id="log",
    name="natural logarithm",
    signature={
        "inputs": {"x": "positive rational"},
        "outputs": {"value": "certified rational enclosure of log(x)"},
    },
    semantics="value is a certified rational enclosure of the natural logarithm for x > 0.",
    reference={
        "kind": "certified-interval",
        "expression": "log_q(x)",
        "path": "cent_compiler/interval.py",
    },
    tolerance="1/10000",
    tests=(
        OperationTest(
            id="log-one",
            kind="exact",
            inputs={"x": "1"},
            expected="0",
            tolerance="0",
            provenance=("tests/test_core.py",),
        ),
    ),
    target_constraints={
        "targets": ["glm-reference"],
        "target_validation": (
            "log-domain-arithmetic reference adapter with fixed vectors; "
            "positive inputs only and a declared enclosure tolerance"
        ),
    },
    provenance=("cent_compiler/interval.py", "tests/test_core.py"),
    gaps=(
        "target evidence is a software reference enclosure with tolerance "
        "1/10000, not a measured junction",
    ),
)

RECIPROCAL = OperationContract(
    id="reciprocal",
    name="exact reciprocal",
    signature={
        "inputs": {"x": "nonzero rational"},
        "outputs": {"value": "rational"},
    },
    semantics="value = 1 / x under exact rational arithmetic; x is nonzero.",
    reference={
        "kind": "exact-arithmetic",
        "expression": "reciprocal(x)",
        "path": "cent_compiler/exact.py",
    },
    tolerance="0",
    tests=(
        OperationTest(
            id="reciprocal-three-quarters",
            kind="exact",
            inputs={"x": "3/4"},
            expected="4/3",
            tolerance="0",
            provenance=("tests/test_transfer_contracts.py",),
        ),
    ),
    target_constraints={
        "targets": ["glm-reference"],
        "target_validation": (
            "log-domain-arithmetic reference adapter with fixed vectors; "
            "positive inputs only and a declared enclosure tolerance"
        ),
    },
    provenance=("cent_compiler/exact.py", "tests/test_transfer_contracts.py"),
    gaps=(
        "target evidence is a positive-input software reference enclosure with "
        "tolerance 1/10000, not a measured junction",
        "negative reciprocal is not declared by the positive log-domain route",
    ),
)

SIGN = OperationContract(
    id="sign",
    name="exact sign",
    signature={
        "inputs": {"x": "rational"},
        "outputs": {"value": "integer in {-1, 0, 1}"},
    },
    semantics="value is -1, 0 or 1 according to the sign of x.",
    reference={
        "kind": "exact-arithmetic",
        "expression": "sign(x)",
        "path": "cent_compiler/exact.py",
    },
    tolerance="0",
    tests=(
        OperationTest(
            id="sign-negative-half",
            kind="exact",
            inputs={"x": "-5/2"},
            expected=-1,
            tolerance="0",
            provenance=("tests/test_transfer_contracts.py",),
        ),
    ),
    target_constraints={
        "targets": ["glm-reference"],
        "target_validation": "reference-adapter-implemented; live not declared",
    },
    provenance=("cent_compiler/exact.py", "tests/test_transfer_contracts.py"),
    gaps=(
        "target evidence is a software reference only; no measured comparator",
        "comparator offset, hysteresis and metastability are not modeled",
    ),
)

OPERATION_CONTRACTS = (
    SQRT, SUM, DIFFERENCE, QUANTIZED_CARRY,
    MULT, DIV, EXP, LOG, RECIPROCAL, SIGN,
)
OPERATION_BY_ID = {contract.id: contract for contract in OPERATION_CONTRACTS}
if len(OPERATION_BY_ID) != len(OPERATION_CONTRACTS):
    raise RuntimeError("operation registry contains duplicate ids")
for _contract in OPERATION_CONTRACTS:
    _contract.validate()


def get_operation(operation_id: str) -> OperationContract:
    """Return a production operation contract or a keyed unknown error."""
    key = str(operation_id).strip()
    try:
        return OPERATION_BY_ID[key]
    except KeyError as exc:
        known = ", ".join(sorted(OPERATION_BY_ID))
        raise KeyError(f"unknown operation contract {key!r}; known: {known}") from exc


# ---------------------------------------------------------------------------
# Explicit behavior signatures
# ---------------------------------------------------------------------------

OPERATION_BEHAVIORS: dict[str, BehaviorSignature] = {
    "sqrt": BehaviorSignature(
        primitive_chain=("sqrt",),
        stateful=False,
        feedback=False,
        conserved_quantities=(),
        nonlinearity="square-root",
        encoding="scalar",
        precision="certified enclosure",
    ),
    "sum": BehaviorSignature(
        primitive_chain=("sum",),
        stateful=False,
        feedback=False,
        conserved_quantities=("signed sum",),
        nonlinearity="linear",
        encoding="scalar",
        precision="exact rational",
    ),
    "difference": BehaviorSignature(
        primitive_chain=("sum", "neg"),
        stateful=False,
        feedback=False,
        conserved_quantities=("signed sum",),
        nonlinearity="linear",
        encoding="scalar",
        precision="exact rational",
    ),
    "quantized_carry": BehaviorSignature(
        primitive_chain=("accum", "quantize", "sum"),
        stateful=True,
        feedback=True,
        conserved_quantities=("first-moment reconstruction",),
        nonlinearity="uniform quantization",
        encoding="bitstream",
        precision="declared quantum",
    ),
    "mult": BehaviorSignature(
        primitive_chain=("mult",),
        stateful=False,
        feedback=False,
        conserved_quantities=("scalar product",),
        nonlinearity="bilinear",
        encoding="scalar",
        precision="exact rational",
    ),
    "div": BehaviorSignature(
        primitive_chain=("div",),
        stateful=False,
        feedback=False,
        conserved_quantities=(),
        nonlinearity="rational division",
        encoding="scalar",
        precision="exact rational",
    ),
    "exp": BehaviorSignature(
        primitive_chain=("exp",),
        stateful=False,
        feedback=False,
        conserved_quantities=(),
        nonlinearity="exponential",
        encoding="scalar",
        precision="certified enclosure",
    ),
    "log": BehaviorSignature(
        primitive_chain=("log",),
        stateful=False,
        feedback=False,
        conserved_quantities=(),
        nonlinearity="logarithmic",
        encoding="positive scalar",
        precision="certified enclosure",
    ),
    "reciprocal": BehaviorSignature(
        primitive_chain=("div",),
        stateful=False,
        feedback=False,
        conserved_quantities=(),
        nonlinearity="rational reciprocal",
        encoding="scalar",
        precision="exact rational",
    ),
    "sign": BehaviorSignature(
        primitive_chain=("sign",),
        stateful=False,
        feedback=False,
        conserved_quantities=("sign",),
        nonlinearity="piecewise constant",
        encoding="scalar",
        precision="exact sign",
    ),
}

MECHANISM_BEHAVIORS: dict[str, BehaviorSignature] = {
    "delta-sigma-error-feedback": BehaviorSignature(
        primitive_chain=("neg", "sum", "accum", "quantize", "sat", "delay"),
        stateful=True,
        feedback=True,
        conserved_quantities=("first-moment reconstruction",),
        nonlinearity="uniform quantization",
        encoding="bitstream",
        precision="declared quantum",
    ),
    "rotational-w4-noise-shaping": BehaviorSignature(
        primitive_chain=("neg", "sum", "accum", "quantize", "sat", "delay"),
        stateful=True,
        feedback=True,
        conserved_quantities=("first-moment reconstruction",),
        nonlinearity="uniform quantization",
        encoding="angular-velocity code",
        precision="declared quantum",
    ),
    "mechanics-noise-shaping": BehaviorSignature(
        primitive_chain=("neg", "sum", "accum", "quantize", "sat", "delay"),
        stateful=True,
        feedback=True,
        conserved_quantities=("first-moment reconstruction",),
        nonlinearity="uniform quantization",
        encoding="velocity code",
        precision="declared quantum",
    ),
    "rheology-continuity": BehaviorSignature(
        primitive_chain=("sum", "neg"),
        stateful=False,
        feedback=False,
        conserved_quantities=("signed strain_rate sum",),
        nonlinearity="linear",
        encoding="normalized scalar",
        precision="exact rational",
    ),
    "log-domain-sqrt": BehaviorSignature(
        primitive_chain=("log", "scale", "exp"),
        stateful=False,
        feedback=False,
        conserved_quantities=(),
        nonlinearity="logarithmic/exponential",
        encoding="normalized scalar",
        precision="certified rational enclosure",
    ),
    "kcl-conservation": BehaviorSignature(
        primitive_chain=("sum", "neg"),
        stateful=False,
        feedback=False,
        conserved_quantities=("signed current sum",),
        nonlinearity="linear",
        encoding="normalized scalar",
        precision="exact rational",
    ),
    "opamp-summing": BehaviorSignature(
        primitive_chain=("sum", "neg"),
        stateful=False,
        feedback=False,
        conserved_quantities=("signed voltage sum",),
        nonlinearity="linear",
        encoding="normalized scalar",
        precision="exact rational",
    ),
    "fluid-continuity": BehaviorSignature(
        primitive_chain=("sum", "neg"),
        stateful=False,
        feedback=False,
        conserved_quantities=("signed flow sum",),
        nonlinearity="linear",
        encoding="normalized scalar",
        precision="exact rational",
    ),
    "log-domain-arithmetic": BehaviorSignature(
        primitive_chain=("log", "sum", "neg", "exp"),
        stateful=False,
        feedback=False,
        conserved_quantities=("log-domain value",),
        nonlinearity="logarithmic/exponential",
        encoding="log-domain",
        precision="certified rational enclosure",
    ),
    "cam-profile": BehaviorSignature(
        primitive_chain=("spatial",),
        stateful=False,
        feedback=False,
        conserved_quantities=(),
        nonlinearity="shaped profile",
        encoding="position",
        precision="declared displacement",
    ),
    "orifice-pressure-flow": BehaviorSignature(
        primitive_chain=("mult", "eq"),
        stateful=False,
        feedback=True,
        conserved_quantities=(),
        nonlinearity="nonlinear pressure/flow restriction",
        encoding="pressure/flow",
        precision="declared pressure/flow range",
    ),
    "pll-phase-tracking": BehaviorSignature(
        primitive_chain=("accum", "wrap", "sum", "scale"),
        stateful=True,
        feedback=True,
        conserved_quantities=("phase error",),
        nonlinearity="sinusoidal phase detector",
        encoding="phase",
        precision="float simulation",
    ),
    "threshold-comparator": BehaviorSignature(
        primitive_chain=("sat", "sum"),
        stateful=False,
        feedback=False,
        conserved_quantities=("sign",),
        nonlinearity="piecewise constant",
        encoding="scalar",
        precision="exact sign",
    ),
}

if set(OPERATION_BEHAVIORS) != set(OPERATION_BY_ID):
    raise RuntimeError("operation behavior table does not match the operation registry")
if set(MECHANISM_BEHAVIORS) != set(MECHANISM_BY_ID):
    raise RuntimeError("mechanism behavior table does not match the mechanism registry")
for _signature in OPERATION_BEHAVIORS.values():
    _signature.validate()
for _mechanism_id, _signature in MECHANISM_BEHAVIORS.items():
    _signature.validate()
    _card = MECHANISM_BY_ID[_mechanism_id]
    if (
        _signature.primitive_chain != _card.primitive_chain
        or _signature.stateful != _card.stateful
    ):
        raise RuntimeError(f"mechanism behavior does not match card: {_mechanism_id}")


# ---------------------------------------------------------------------------
# Target and mapping operators
# ---------------------------------------------------------------------------

REFERENCE_TARGET = GLM_REFERENCE_TARGET
TARGET_PROFILES = {
    REFERENCE_TARGET.id: REFERENCE_TARGET,
    GLM_LIVE_TARGET.id: GLM_LIVE_TARGET,
}
REFERENCE_TARGET.validate()
GLM_LIVE_TARGET.validate()


def get_target_profile(target_id: str) -> TargetProfile:
    key = str(target_id).strip()
    try:
        return TARGET_PROFILES[key]
    except KeyError as exc:
        known = ", ".join(sorted(TARGET_PROFILES))
        raise KeyError(f"unknown target profile {key!r}; known: {known}") from exc




# ---------------------------------------------------------------------------
# Structural retrieval
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RetrievalMatch:
    score: int
    reasons: tuple[str, ...]


_TOKENS = re.compile(r"[a-z0-9]+")


def _tokens(value: str) -> set[str]:
    return set(_TOKENS.findall(value.lower()))


def _overlap(left: str, right: str) -> bool:
    return bool(_tokens(left) & _tokens(right))


def _score(operation: OperationContract, card: MechanismCard) -> RetrievalMatch:
    behavior = OPERATION_BEHAVIORS[operation.id]
    mechanism = MECHANISM_BEHAVIORS[card.id]
    reasons = []
    score = 10

    overlap = set(behavior.primitive_chain) & set(mechanism.primitive_chain)
    if overlap:
        score += 2 * len(overlap)
        reasons.append("primitive overlap: " + ", ".join(sorted(overlap)))
    if behavior.stateful == mechanism.stateful:
        score += 3
        reasons.append(f"stateful {str(behavior.stateful).lower()} match")
    if behavior.feedback == mechanism.feedback:
        score += 3
        reasons.append(f"feedback {str(behavior.feedback).lower()} match")
    if _overlap(behavior.encoding, mechanism.encoding):
        score += 1
        reasons.append("encoding overlap")
    if _overlap(behavior.nonlinearity, mechanism.nonlinearity):
        score += 1
        reasons.append("nonlinearity overlap")
    if _overlap(behavior.precision, mechanism.precision):
        score += 1
        reasons.append("precision overlap")
    if set(behavior.conserved_quantities) & set(mechanism.conserved_quantities):
        score += 2
        reasons.append("conserved-quantity overlap")
    if operation.id in card.supported_operations:
        score += 2
        reasons.append(
            f"card declares {operation.id} support "
            "(mechanism metadata; weak rank signal)"
        )
    if not reasons:
        reasons.append("base structural score only")
    return RetrievalMatch(score=score, reasons=tuple(reasons))


def _steps(
    operation: OperationContract,
    target: TargetProfile,
    card: MechanismCard,
) -> tuple[MappingStep, ...]:
    steps = [
        MappingStep(
            source=f"operation {operation.id}",
            target=f"target {target.id} operation",
            law=_OPERATOR_BY_ID["identity"].law,
            kind=_OPERATOR_BY_ID["identity"].kind,
            provenance=card.provenance,
            gaps=_OPERATOR_BY_ID["identity"].gaps,
        )
    ]
    for operator_id in card.operators:
        operator = _OPERATOR_BY_ID[operator_id]
        steps.append(
            MappingStep(
                source=f"generated {card.id} interpretation",
                target=f"{target.id} {operator.kind} model",
                law=operator.law,
                kind=operator.kind,
                provenance=card.provenance,
                gaps=operator.gaps,
            )
        )
    if len(card.primitive_chain) > 1 and "composition" not in card.operators:
        operator = _OPERATOR_BY_ID["composition"]
        steps.append(
            MappingStep(
                source="mechanism primitive chain",
                target="target operation decomposition",
                law=" -> ".join(card.primitive_chain),
                kind=operator.kind,
                provenance=card.provenance,
                gaps=operator.gaps,
            )
        )
    if card.stateful:
        operator = _OPERATOR_BY_ID["state-transform"]
        steps.append(
            MappingStep(
                source="mechanism state",
                target="target state",
                law=operator.law,
                kind=operator.kind,
                provenance=card.provenance,
                gaps=operator.gaps,
            )
        )
    if "quantize" in card.primitive_chain:
        operator = _OPERATOR_BY_ID["sampling-quantization"]
        steps.append(
            MappingStep(
                source="mechanism quantized output",
                target="target bounded code",
                law=operator.law,
                kind=operator.kind,
                provenance=card.provenance,
                gaps=operator.gaps,
            )
        )
    if MECHANISM_BEHAVIORS[card.id].feedback:
        operator = _OPERATOR_BY_ID["feedback-equivalence"]
        steps.append(
            MappingStep(
                source="mechanism feedback path",
                target="target feedback path",
                law=operator.law,
                kind=operator.kind,
                provenance=card.provenance,
                gaps=operator.gaps,
            )
        )
    return tuple(steps)


def _candidate(
    operation: OperationContract,
    target: TargetProfile,
    card: MechanismCard,
    *,
    rank: int,
) -> TransferCandidate:
    candidate = TransferCandidate(
        id=f"{operation.id}-to-{target.id}-via-{card.id}",
        operation=operation.id,
        mechanism=card.id,
        source_domain=card.source_domains[0],
        target=target.id,
        mapping=_steps(operation, target, card),
        preserved=card.invariants,
        relaxed=(),
        relaxation=RelaxationRecord(),
        validity=card.validity,
        evidence_level=card.evidence_level,
        tests=(),
        artifact=None,
        gaps=tuple(dict.fromkeys(card.gaps)),
        status="candidate",
        provenance=tuple(dict.fromkeys((*operation.provenance, *card.provenance))),
        rank=rank,
    )
    candidate.validate(mechanism=card, allow_undeclared=True)
    return candidate


def retrieve(
    operation_id: str,
    *,
    target_id: str = "glm-reference",
    limit: int = DEFAULT_RETRIEVAL_LIMIT,
) -> tuple[
    OperationContract,
    TargetProfile,
    tuple[TransferCandidate, ...],
    dict[str, dict[str, Any]],
]:
    """Return the top ranked candidates for one production operation contract."""
    if limit < 1:
        raise ValueError("limit must be at least one")
    operation = get_operation(operation_id)
    target = get_target_profile(target_id)
    scored: list[tuple[int, MechanismCard, RetrievalMatch]] = []
    for card in MECHANISM_CARDS:
        match = _score(operation, card)
        scored.append((match.score, card, match))
    scored.sort(key=lambda item: (-item[0], item[1].id))
    selected = scored[:limit]

    candidates: list[TransferCandidate] = []
    matches: dict[str, dict[str, Any]] = {}
    for rank, (_score_value, card, match) in enumerate(selected, start=1):
        candidate = _candidate(operation, target, card, rank=rank)
        candidates.append(candidate)
        matches[candidate.id] = {
            "score": match.score,
            "declared_support": operation.id in card.supported_operations,
            "reasons": list(match.reasons),
        }
    return operation, target, tuple(candidates), matches


def transfer_payload(
    operation_id: str,
    *,
    target_id: str = "glm-reference",
    limit: int = DEFAULT_RETRIEVAL_LIMIT,
) -> dict[str, Any]:
    """Build the JSON view for ``cent transfer`` without target claims."""
    operation, target, candidates, matches = retrieve(
        operation_id, target_id=target_id, limit=limit
    )
    domains = sorted({candidate.source_domain for candidate in candidates})
    relaxation_counts = {name: 0 for name in sorted(RELAXATION_CLASSES)}
    for candidate in candidates:
        relaxation_counts[candidate.relaxation.classification] += 1
    checks = [
        {
            "name": "mechanism retrieval",
            "status": "pass" if candidates else "gap",
            "detail": f"{len(candidates)} candidate(s) from {len(domains)} domain(s)",
        }
    ]
    gaps = [
        "candidates are unvalidated; no target artifact or target test is implemented",
        "scale/offset and effort-flow mapping operators are declared but not applied",
        "no GLM performance, integration or measured-device claim is made",
    ]
    return {
        "ok": True,
        "schema": RESULT_SCHEMA,
        "operation": operation.as_dict(),
        "target": target.as_dict(),
        "behaviors": {
            "operation": OPERATION_BEHAVIORS[operation.id].as_dict(),
            "mechanisms": {
                candidate.mechanism: MECHANISM_BEHAVIORS[candidate.mechanism].as_dict()
                for candidate in candidates
            },
        },
        "operators": [operator.as_dict() for operator in MAPPING_OPERATORS],
        "candidates": [candidate.as_dict() for candidate in candidates],
        "matches": matches,
        "summary": {
            "candidates": len(candidates),
            "domains": domains,
            "mechanisms": [candidate.mechanism for candidate in candidates],
            "relaxation_classes": relaxation_counts,
            "candidate_only": True,
        },
        "checks": checks,
        "gaps": gaps,
        "headline": (
            f"{len(candidates)} transfer candidate(s) for {operation.id} "
            f"across {len(domains)} domain(s); none is validated."
        ),
    }


def render_transfer(payload: Mapping[str, Any]) -> str:
    """Render a transfer result without implying target validation."""
    operation = payload.get("operation") or {}
    target = payload.get("target") or {}
    lines = ["=" * 78, "TRANSFER RETRIEVAL", "=" * 78]
    lines.append(str(payload.get("headline", "")))
    lines.append(
        f"operation: {operation.get('id')} · target: {target.get('id')}"
    )
    lines.append("")
    for candidate in payload.get("candidates", ()):
        match = (payload.get("matches") or {}).get(candidate.get("id"), {})
        lines.append(
            f"{candidate.get('rank')}. {candidate.get('mechanism')} "
            f"[{candidate.get('evidence_level')}] "
            f"domain={candidate.get('source_domain')} score={match.get('score')}"
        )
        relaxation = candidate.get("relaxation") or {}
        lines.append(
            f"  relaxation: {relaxation.get('classification')} "
            f"({relaxation.get('evidence_level')})"
        )
        lines.append(
            "  reasons: " + "; ".join(match.get("reasons") or ())
        )
        first_gap = (candidate.get("gaps") or ["no gap declared"])[0]
        lines.append(f"  first gap: {first_gap}")
        lines.append("")
    if not payload.get("candidates"):
        lines.append("No scored mechanism candidate was returned.")
        lines.append("")
    lines.append("No target artifact, target test or validated transfer is claimed.")
    return "\n".join(lines)
