"""Tier-D refutation: generate negatives with explicit witness pairs.

The rule is narrow and testable:

    If two instances share a declared signature but differ in their required
    observable, then no map through that signature alone exists.

The generator never invents an external law.  It pairs declared instances,
finds a signature they genuinely share, and records the exact observable where
they diverge.  The Q-tensor retirement is reproduced from its two directors;
the carry witness is the two-tick/one-tick timing distinction; the junction
witnesses are the current/voltage/flow carriers.

A test obligation is *derived* from an operation contract or a witness, not
authored as a separate list of expected cases.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Iterable, Mapping

from .transfer_evaluation import NEGATIVE_CONTROLS
from .transfer_engine import get_operation

SCHEMA = "cent-tier-d-ledger/1"
WITNESS_SCHEMA = "cent-tier-d-witness/1"
OBLIGATION_SCHEMA = "cent-tier-d-obligation/1"


@dataclass(frozen=True)
class WitnessInstance:
    """One declared instance and the observable it is required to produce."""

    id: str
    kind: str
    signature: tuple[str, ...]
    observable: Mapping[str, str]
    provenance: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.kind.strip():
            raise ValueError("witness instance needs an id and kind")
        if not self.signature:
            raise ValueError(f"{self.id}: signature must not be empty")
        if not self.observable:
            raise ValueError(f"{self.id}: observable must not be empty")
        object.__setattr__(self, "signature", tuple(self.signature))
        object.__setattr__(self, "observable", dict(self.observable))
        object.__setattr__(self, "provenance", tuple(self.provenance))

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "signature": list(self.signature),
            "observable": dict(self.observable),
            "provenance": list(self.provenance),
        }


@dataclass(frozen=True)
class WitnessPair:
    """A generated negative: equal signature, unequal required observable."""

    id: str
    signature: tuple[str, ...]
    left: str
    right: str
    probe: str
    left_value: str
    right_value: str
    conclusion: str
    provenance: tuple[str, ...]
    retire_lead: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": WITNESS_SCHEMA,
            "id": self.id,
            "kind": "generated-negative",
            "signature": list(self.signature),
            "witness": {
                "left": self.left,
                "right": self.right,
                "probe": self.probe,
                "left_value": self.left_value,
                "right_value": self.right_value,
            },
            "conclusion": self.conclusion,
            "retire_lead": self.retire_lead,
            "provenance": list(self.provenance),
        }


def _instances() -> tuple[WitnessInstance, ...]:
    """The declared witness corpus, grouped by the signature each pair shares."""
    return (
        WitnessInstance(
            id="nematic-q-director-x",
            kind="q-tensor",
            signature=("q-invariant:S=1", "q-invariant:tr(Q^2)=2/1", "q-invariant:det(Q)=-1/1"),
            observable={"area": "2/1", "director": "(1,0)"},
            provenance=("docs/evidence/nematic-q-tensor/check.py",),
        ),
        WitnessInstance(
            id="nematic-q-director-3-4",
            kind="q-tensor",
            signature=("q-invariant:S=1", "q-invariant:tr(Q^2)=2/1", "q-invariant:det(Q)=-1/1"),
            observable={"area": "66/25", "director": "(3/5,4/5)"},
            provenance=("docs/evidence/nematic-q-tensor/check.py",),
        ),
        WitnessInstance(
            id="kcl-conservation",
            kind="mechanism",
            signature=("junction:sum-neg", "stateful:false", "feedback:false"),
            observable={"carrier": "current", "law": "signed current sum"},
            provenance=("cent_compiler/mechanisms.py",),
        ),
        WitnessInstance(
            id="opamp-summing",
            kind="mechanism",
            signature=("junction:sum-neg", "stateful:false", "feedback:false"),
            observable={"carrier": "voltage", "law": "signed voltage sum"},
            provenance=("cent_compiler/mechanisms.py",),
        ),
        WitnessInstance(
            id="fluid-continuity",
            kind="mechanism",
            signature=("junction:sum-neg", "stateful:false", "feedback:false"),
            observable={"carrier": "flow", "law": "signed flow sum"},
            provenance=("cent_compiler/mechanisms.py",),
        ),
        WitnessInstance(
            id="log-domain-sqrt",
            kind="mechanism",
            signature=("nonlinearity:log-exp", "stateful:false", "feedback:false"),
            observable={"operation": "sqrt", "program": "log -> scale(1/2) -> exp"},
            provenance=("cent_compiler/mechanisms.py", "cent_compiler/assembly.py"),
        ),
        WitnessInstance(
            id="log-domain-arithmetic",
            kind="mechanism",
            signature=("nonlinearity:log-exp", "stateful:false", "feedback:false"),
            observable={"operation": "arithmetic", "program": "log -> sum/neg -> exp"},
            provenance=("cent_compiler/mechanisms.py", "cent_compiler/assembly.py"),
        ),
        WitnessInstance(
            id="two-tick-quantized-carry",
            kind="target",
            signature=("carrier:quantized-feedback", "stateful:true", "feedback:true"),
            observable={"code@1/2": "1,1,1,0,0,0", "timing": "two-tick"},
            provenance=("cent_compiler/targets/glm.py", "docs/evidence/bresenham/check.py"),
        ),
        WitnessInstance(
            id="one-tick-floor-carry",
            kind="target",
            signature=("carrier:quantized-feedback", "stateful:true", "feedback:true"),
            observable={"code@1/2": "0,1,0,1,0,1", "timing": "one-tick"},
            provenance=("cent_compiler/quantized_carry_floor.py", "docs/evidence/bresenham/check.py"),
        ),
        WitnessInstance(
            id="mult",
            kind="operation",
            signature=("law-family:multiplicative", "stateful:false", "feedback:false", "exact:rational"),
            observable={"law": "a*b", "arity": "2"},
            provenance=("cent_compiler/transfer_engine.py",),
        ),
        WitnessInstance(
            id="div",
            kind="operation",
            signature=("law-family:multiplicative", "stateful:false", "feedback:false", "exact:rational"),
            observable={"law": "a/b", "arity": "2"},
            provenance=("cent_compiler/transfer_engine.py",),
        ),
        WitnessInstance(
            id="sum",
            kind="operation",
            signature=("law-family:additive", "stateful:false", "feedback:false", "exact:rational"),
            observable={"law": "a+b", "arity": "2"},
            provenance=("cent_compiler/transfer_engine.py",),
        ),
        WitnessInstance(
            id="difference",
            kind="operation",
            signature=("law-family:additive", "stateful:false", "feedback:false", "exact:rational"),
            observable={"law": "a-b", "arity": "2"},
            provenance=("cent_compiler/transfer_engine.py",),
        ),
    )


def _slug(value: str) -> str:
    return "".join(character if character.isalnum() else "-" for character in value.lower()).strip("-")


def _first_difference(left: Mapping[str, str], right: Mapping[str, str]) -> tuple[str, str, str] | None:
    for key in sorted(set(left) | set(right)):
        if left.get(key) != right.get(key):
            return key, str(left.get(key, "")), str(right.get(key, ""))
    return None


def _conclusion(left: WitnessInstance, right: WitnessInstance, probe: str) -> str:
    if left.kind == "q-tensor":
        return (
            f"the scalar Q-tensor invariants are identical while {probe!r} differs "
            f"({left.observable.get(probe)} vs {right.observable.get(probe)}); "
            "no invariant-only map through this signature exists"
        )
    if "junction:sum-neg" in left.signature:
        return (
            "the shared sum/neg junction signature does not determine whether the "
            f"conserved observable is current, voltage or flow ({probe} differs); "
            "no map through that signature alone exists"
        )
    if "nonlinearity:log-exp" in left.signature:
        return (
            "a shared log/exp signature does not determine whether the route computes "
            f"sqrt or arithmetic ({probe} differs); no map through that signature alone exists"
        )
    if "carrier:quantized-feedback" in left.signature:
        return (
            "a shared stateful quantized-feedback signature does not determine the "
            f"one-tick/two-tick code timing ({probe} differs); no map through that signature alone exists"
        )
    return (
        f"the shared declared signature does not determine {probe!r} "
        f"({left.observable.get(probe)} vs {right.observable.get(probe)}); "
        "no map through that signature alone exists"
    )


def generate_witnesses(
    instances: Iterable[WitnessInstance] | None = None,
) -> tuple[WitnessPair, ...]:
    """Pair every equal-signature group and retain only observable separations."""
    corpus = tuple(instances or _instances())
    ids = [instance.id for instance in corpus]
    if len(ids) != len(set(ids)):
        raise ValueError("witness corpus contains duplicate instance ids")
    groups: dict[tuple[str, ...], list[WitnessInstance]] = {}
    for instance in corpus:
        groups.setdefault(instance.signature, []).append(instance)
    witnesses: list[WitnessPair] = []
    for signature, group in groups.items():
        for left, right in combinations(group, 2):
            difference = _first_difference(left.observable, right.observable)
            if difference is None:
                continue
            probe, left_value, right_value = difference
            witnesses.append(
                WitnessPair(
                    id=f"tier-d-{_slug(left.id)}-vs-{_slug(right.id)}",
                    signature=signature,
                    left=left.id,
                    right=right.id,
                    probe=probe,
                    left_value=left_value,
                    right_value=right_value,
                    conclusion=_conclusion(left, right, probe),
                    provenance=tuple(dict.fromkeys((*left.provenance, *right.provenance))),
                    retire_lead=(
                        "nematic-q-tensor-bounding-box"
                        if left.kind == "q-tensor"
                        else ""
                    ),
                )
            )
    return tuple(witnesses)


@dataclass(frozen=True)
class TestObligation:
    id: str
    kind: str
    assertion: str
    derived_from: str
    authored: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": OBLIGATION_SCHEMA,
            "id": self.id,
            "kind": self.kind,
            "assertion": self.assertion,
            "derived_from": self.derived_from,
            "authored": self.authored,
        }


def derive_contract_obligations(operation_id: str = "quantized_carry") -> tuple[TestObligation, ...]:
    """Derive test obligations from an operation contract's declared fields."""
    contract = get_operation(operation_id)
    outputs = contract.signature.get("outputs") or {}
    obligations: list[TestObligation] = []
    code_description = str(outputs.get("code", ""))
    if "bounded" in code_description.lower():
        obligations.append(
            TestObligation(
                id=f"{operation_id}-bounded-state",
                kind="bounded-state",
                assertion=(
                    "For every fixed vector, each emitted code is a declared "
                    "quantizer level and the feedback state remains bounded."
                ),
                derived_from=(
                    f"cent-operation/1 {operation_id} signature.outputs.code = "
                    f"{code_description}"
                ),
            )
        )
    mean_description = str(outputs.get("mean", ""))
    if mean_description:
        obligations.append(
            TestObligation(
                id=f"{operation_id}-mean-reconstruction",
                kind="mean-reconstruction",
                assertion=(
                    "The fixed-vector code mean reconstructs the declared input "
                    "within the contract's tolerance."
                ),
                derived_from=(
                    f"cent-operation/1 {operation_id} signature.outputs.mean = "
                    f"{mean_description}"
                ),
            )
        )
    return tuple(obligations)


def derive_witness_obligations(witnesses: Iterable[WitnessPair]) -> tuple[TestObligation, ...]:
    """Derive an observable-separation assertion from every witness pair."""
    return tuple(
        TestObligation(
            id=f"{witness.id}-separation",
            kind="observable-separation",
            assertion=(
                f"Assert observable[{witness.probe!r}] differs between "
                f"{witness.left!r} ({witness.left_value!r}) and "
                f"{witness.right!r} ({witness.right_value!r})."
            ),
            derived_from=f"{WITNESS_SCHEMA} {witness.id}",
        )
        for witness in witnesses
    )


def build_ledger(instances: Iterable[WitnessInstance] | None = None) -> dict[str, Any]:
    """Build the complete Tier-D ledger with generated negatives and obligations."""
    corpus = tuple(instances or _instances())
    witnesses = generate_witnesses(corpus)
    contract_obligations = derive_contract_obligations()
    witness_obligations = derive_witness_obligations(witnesses)
    hand_declared = len(NEGATIVE_CONTROLS)
    retired = [
        {
            "lead_id": witness.retire_lead,
            "decision": "retire",
            "witness": witness.id,
            "reason": witness.conclusion,
        }
        for witness in witnesses
        if witness.retire_lead
    ]
    obligations = (*contract_obligations, *witness_obligations)
    ok = (
        len(witnesses) > hand_declared
        and len(retired) == 1
        and all(obligation.authored is False for obligation in obligations)
    )
    return {
        "schema": SCHEMA,
        "generator": "tier-d-witness-search",
        "ok": ok,
        "instances": [instance.as_dict() for instance in corpus],
        "negatives": [witness.as_dict() for witness in witnesses],
        "summary": {
            "instances": len(corpus),
            "generated_negatives": len(witnesses),
            "hand_declared_negatives": hand_declared,
            "exceeds_hand_declared": len(witnesses) > hand_declared,
            "derived_obligations": len(obligations),
            "authored_obligations": sum(obligation.authored for obligation in obligations),
            "retired_leads": len(retired),
        },
        "retired_leads": retired,
        "obligations": [obligation.as_dict() for obligation in obligations],
    }


def write_ledger(path: str, payload: Mapping[str, Any] | None = None) -> str:
    import json
    from pathlib import Path

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload or build_ledger(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(target)


def render_ledger(payload: Mapping[str, Any] | None = None) -> str:
    ledger = payload or build_ledger()
    summary = ledger.get("summary") or {}
    lines = ["=" * 78, "TIER-D REFUTATION LEDGER", "=" * 78]
    lines.append(
        f"instances: {summary.get('instances')} · generated negatives: "
        f"{summary.get('generated_negatives')} · hand-declared: "
        f"{summary.get('hand_declared_negatives')} · exceeds: "
        f"{summary.get('exceeds_hand_declared')}"
    )
    lines.append("")
    for negative in ledger.get("negatives") or ():
        witness = negative.get("witness") or {}
        lines.append(f"{negative.get('id')} · {negative.get('kind')}")
        lines.append(
            f"  shared signature: {', '.join(negative.get('signature') or ())}"
        )
        lines.append(
            f"  witness: {witness.get('left')} vs {witness.get('right')} · "
            f"{witness.get('probe')}: {witness.get('left_value')} vs "
            f"{witness.get('right_value')}"
        )
        lines.append(f"  conclusion: {negative.get('conclusion')}")
        if negative.get("retire_lead"):
            lines.append(f"  retires: {negative.get('retire_lead')}")
        lines.append("")
    lines.append("Derived test obligations")
    for obligation in ledger.get("obligations") or ():
        lines.append(
            f"  {obligation.get('id')} [{obligation.get('kind')}] "
            f"authored={obligation.get('authored')}"
        )
        lines.append(f"    {obligation.get('assertion')}")
    return "\n".join(lines)


__all__ = [
    "OBLIGATION_SCHEMA",
    "SCHEMA",
    "WITNESS_SCHEMA",
    "TestObligation",
    "WitnessInstance",
    "WitnessPair",
    "build_ledger",
    "derive_contract_obligations",
    "derive_witness_obligations",
    "generate_witnesses",
    "render_ledger",
    "write_ledger",
]
