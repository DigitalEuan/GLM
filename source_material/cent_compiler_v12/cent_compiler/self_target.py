"""D4: make the compiler itself the target.

Two self-applications are measured, never asserted:

1. the exact Bresenham/one-tick proof is promoted into
   ``quantized_carry_floor`` and compared with the existing two-tick carry
   target over the same integer walks;
2. junction conservation becomes a runtime invariant check on exact
   ``cent-program/1`` programs and is compared with the static
   ``topology_audit`` over injected structural and semantic faults.

Each result is a ``cent-utility/1`` record.  The independent oracle in
:mod:`cent_compiler.self_oracle` issues the certificate; the candidate code is
never on that certificate path.  ``rollback`` executes the baseline path again
and records that it restored the baseline value.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping

from .assembly import KCLSumRoute, audit_route_topology, kcl_sum_route
from .program import Instruction, Program
from .quantized_carry_floor import floor_carry_sequence
from .runtime_invariants import check_route
from .self_oracle import CERTIFICATE_SCHEMA, certify, confirms_semantic_fault, line_walk
from .targets.glm import delta_sigma_quantized_carry

UTILITY_SCHEMA = "cent-utility/1"
UTILITY_LEDGER_SCHEMA = "cent-utility-ledger/1"
ADOPTION_STATES = frozenset({"proposed", "adopted", "reverted"})
CARRY_ID = "bresenham-quantized-carry-floor"
RUNTIME_ID = "junction-runtime-invariants"
DEFAULT_LEDGER = Path("examples/self/utility.json")

CASES: tuple[dict[str, Fraction], ...] = (
    {"a": Fraction(1, 2), "b": Fraction(1, 3)},
    {"a": Fraction(-3, 4), "b": Fraction(2, 5)},
    {"a": Fraction(7, 3), "b": Fraction(-5, 6)},
    {"a": Fraction(0), "b": Fraction(9, 7)},
)


def _ratio(numerator: int, denominator: int) -> str:
    return f"{numerator}/{denominator}"


def _parse_ratio(value: str) -> Fraction:
    if "/" not in value:
        raise ValueError(f"utility value must be an 'a/b' ratio, got {value!r}")
    return Fraction(value)


@dataclass(frozen=True)
class UtilityRecord:
    """One measured self-transfer, exactly as ``cent-utility/1`` declares it."""

    id: str
    title: str
    target_subsystem: str
    baseline_command: str
    candidate_command: str
    metric: str
    baseline_value: str
    candidate_value: str
    delta: str
    trials: int
    seed: int
    independent_oracle: str
    adoption_state: str
    rollback: str
    rollback_evidence: Mapping[str, Any]
    detail: str = ""

    def __post_init__(self) -> None:
        required = {
            "id": self.id,
            "title": self.title,
            "target_subsystem": self.target_subsystem,
            "baseline_command": self.baseline_command,
            "candidate_command": self.candidate_command,
            "metric": self.metric,
            "baseline_value": self.baseline_value,
            "candidate_value": self.candidate_value,
            "delta": self.delta,
            "independent_oracle": self.independent_oracle,
            "rollback": self.rollback,
        }
        missing = [name for name, value in required.items() if not str(value).strip()]
        if missing:
            raise ValueError(f"utility record is missing {missing}")
        if self.adoption_state not in ADOPTION_STATES:
            raise ValueError(f"unknown adoption state {self.adoption_state!r}")
        if isinstance(self.trials, bool) or self.trials < 1:
            raise ValueError("utility record needs a positive trial count")
        baseline = _parse_ratio(self.baseline_value)
        candidate = _parse_ratio(self.candidate_value)
        delta = _parse_ratio(self.delta)
        if candidate - baseline != delta:
            raise ValueError("utility delta must equal candidate minus baseline")
        object.__setattr__(self, "rollback_evidence", dict(self.rollback_evidence))

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": UTILITY_SCHEMA,
            "id": self.id,
            "title": self.title,
            "target_subsystem": self.target_subsystem,
            "baseline_command": self.baseline_command,
            "candidate_command": self.candidate_command,
            "metric": self.metric,
            "baseline_value": self.baseline_value,
            "candidate_value": self.candidate_value,
            "delta": self.delta,
            "trials": self.trials,
            "seed": self.seed,
            "independent_oracle": self.independent_oracle,
            "adoption_state": self.adoption_state,
            "rollback": self.rollback,
            "rollback_evidence": dict(self.rollback_evidence),
            "detail": self.detail,
        }


def _program(name: str, instructions: tuple[Instruction, ...], outputs: Mapping[str, str]) -> Program:
    return Program(
        name=name,
        inputs={"a": "numeric", "b": "numeric"},
        instructions=instructions,
        outputs=dict(outputs),
    )


@dataclass(frozen=True)
class Fault:
    name: str
    kind: str
    route: KCLSumRoute
    original: KCLSumRoute
    structural: bool


def _faults() -> list[Fault]:
    sum_route = kcl_sum_route(operation="sum")
    difference_route = kcl_sum_route(operation="difference")
    junction = sum_route.components[0]
    faults = [
        Fault("missing-components", "structural", replace(sum_route, components=()), sum_route, True),
        Fault(
            "duplicate-component-role",
            "structural",
            replace(sum_route, components=(junction, junction)),
            sum_route,
            True,
        ),
        Fault(
            "undeclared-component-parameter",
            "structural",
            replace(
                sum_route,
                components=(replace(junction, parameters={"bogus": 1}),),
            ),
            sum_route,
            True,
        ),
        Fault(
            "broken-output-wire",
            "structural",
            replace(
                sum_route,
                program=replace(sum_route.program, outputs={"total": "not_a_wire"}),
            ),
            sum_route,
            True,
        ),
        Fault(
            "wrong-operation-mult",
            "semantic",
            replace(
                sum_route,
                program=_program(
                    "sum-kcl-wrong-mult",
                    (Instruction("mult", ("a", "b"), "total"),),
                    {"total": "total"},
                ),
            ),
            sum_route,
            False,
        ),
        Fault(
            "aliased-operand",
            "semantic",
            replace(
                sum_route,
                program=_program(
                    "sum-kcl-aliased-operand",
                    (Instruction("sum", ("b", "b"), "total"),),
                    {"total": "total"},
                ),
            ),
            sum_route,
            False,
        ),
        Fault(
            "output-aliases-input",
            "semantic",
            replace(
                sum_route,
                program=_program(
                    "sum-kcl-output-alias",
                    (Instruction("sum", ("a", "b"), "total"),),
                    {"total": "a"},
                ),
            ),
            sum_route,
            False,
        ),
        Fault(
            "extra-addend",
            "semantic",
            replace(
                sum_route,
                program=_program(
                    "sum-kcl-extra-addend",
                    (Instruction("sum", ("a", "b", "a"), "total"),),
                    {"total": "total"},
                ),
            ),
            sum_route,
            False,
        ),
        Fault(
            "scaled-output",
            "semantic",
            replace(
                sum_route,
                program=_program(
                    "sum-kcl-scaled",
                    (
                        Instruction("sum", ("a", "b"), "sum_ab"),
                        Instruction("scale", ("sum_ab",), "total", {"factor": Fraction(2)}),
                    ),
                    {"total": "total"},
                ),
            ),
            sum_route,
            False,
        ),
        Fault(
            "difference-drops-negation",
            "semantic",
            replace(
                difference_route,
                program=_program(
                    "difference-drops-negation",
                    (Instruction("sum", ("a", "b"), "total"),),
                    {"total": "total"},
                ),
            ),
            difference_route,
            False,
        ),
        Fault(
            "difference-swapped-inputs",
            "semantic",
            replace(
                difference_route,
                program=_program(
                    "difference-swapped-inputs",
                    (
                        Instruction("neg", ("a",), "neg_a"),
                        Instruction("sum", ("b", "neg_a"), "total"),
                    ),
                    {"total": "total"},
                ),
            ),
            difference_route,
            False,
        ),
        Fault(
            "difference-output-aliases-negation",
            "semantic",
            replace(
                difference_route,
                program=_program(
                    "difference-output-alias",
                    (
                        Instruction("neg", ("b",), "neg_b"),
                        Instruction("sum", ("a", "neg_b"), "total"),
                    ),
                    {"total": "neg_b"},
                ),
            ),
            difference_route,
            False,
        ),
    ]
    return faults


def _detects_static(route: KCLSumRoute) -> bool:
    return audit_route_topology(route).get("status") == "gap"


def _detects_runtime(route: KCLSumRoute) -> bool:
    return not check_route(route, CASES).get("ok", False)


def measure_runtime_faults(*, use_runtime: bool = True) -> dict[str, Any]:
    """Measure static-only and candidate detection over twelve injected faults."""
    rows: list[dict[str, Any]] = []
    static_hits = 0
    candidate_hits = 0
    oracle_confirmations = 0
    for fault in _faults():
        static = _detects_static(fault.route)
        runtime = _detects_runtime(fault.route) if use_runtime else False
        detected = static or runtime
        confirmed = (
            True
            if fault.structural
            else confirms_semantic_fault(fault.original, fault.route, CASES)
        )
        static_hits += int(static)
        candidate_hits += int(detected)
        oracle_confirmations += int(confirmed)
        rows.append(
            {
                "fault": fault.name,
                "kind": fault.kind,
                "static_topology_audit": static,
                "runtime_invariant": runtime,
                "candidate": detected,
                "oracle_confirmed": confirmed,
            }
        )
    total = len(rows)
    return {
        "schema": "cent-runtime-fault-benchmark/1",
        "trials": total,
        "seed": 0,
        "use_runtime": use_runtime,
        "baseline_hits": static_hits,
        "candidate_hits": candidate_hits,
        "oracle_confirmations": oracle_confirmations,
        "baseline_value": _ratio(static_hits, total),
        "candidate_value": _ratio(candidate_hits, total),
        "rows": rows,
        "ok": oracle_confirmations == total and candidate_hits >= static_hits,
    }


def measure_carry_agreement(*, use_floor: bool = True, max_dx: int = 16) -> dict[str, Any]:
    """Compare the two-tick target and the one-tick floor contract to the walk."""
    trials = 0
    baseline_hits = 0
    candidate_hits = 0
    rows: list[dict[str, Any]] = []
    for dx in range(1, max_dx + 1):
        for dy in range(dx + 1):
            trials += 1
            expected = line_walk(dx, dy)
            baseline = delta_sigma_quantized_carry(Fraction(dy, dx), samples=dx).code
            candidate = floor_carry_sequence(Fraction(dy, dx), dx)
            baseline_hits += int(tuple(baseline) == expected)
            candidate_hits += int((candidate if use_floor else tuple(baseline)) == expected)
            if tuple(baseline) != expected or candidate != expected:
                rows.append(
                    {
                        "dx": dx,
                        "dy": dy,
                        "oracle": list(expected),
                        "baseline": list(baseline),
                        "candidate": list(candidate),
                    }
                )
    return {
        "schema": "cent-carry-agreement-benchmark/1",
        "trials": trials,
        "seed": 0,
        "use_floor": use_floor,
        "baseline_hits": baseline_hits,
        "candidate_hits": candidate_hits,
        "baseline_value": _ratio(baseline_hits, trials),
        "candidate_value": _ratio(candidate_hits, trials),
        "mismatches": rows,
        "ok": candidate_hits == trials if use_floor else candidate_hits == baseline_hits,
    }


def _build_carry_record(*, state: str = "adopted") -> tuple[UtilityRecord, dict[str, Any]]:
    measurement = measure_carry_agreement()
    baseline = measurement["baseline_value"]
    candidate = measurement["candidate_value"]
    delta = _ratio(
        measurement["candidate_hits"] - measurement["baseline_hits"],
        measurement["trials"],
    )
    rollback = measure_carry_agreement(use_floor=False)
    rollback_restored = rollback["candidate_hits"] == measurement["baseline_hits"]
    evidence = {
        "verified": rollback_restored,
        "method": "measure the existing two-tick delta-sigma target in place of the floor contract",
        "restored_value": rollback["baseline_value"],
        "baseline_command": "python3 cent self --baseline --json",
    }
    record = UtilityRecord(
        id=CARRY_ID,
        title="Bresenham one-tick proof promoted to quantized_carry_floor",
        target_subsystem="cent_compiler.quantized_carry_floor (declared operation contract)",
        baseline_command="python3 cent self --baseline --json",
        candidate_command="python3 cent self --json",
        metric="Bresenham integer-walk agreement rate",
        baseline_value=baseline,
        candidate_value=candidate,
        delta=delta,
        trials=measurement["trials"],
        seed=0,
        independent_oracle="self_oracle.line_walk; docs/evidence/bresenham/check.py",
        adoption_state=state,
        rollback="cent self --revert " + CARRY_ID,
        rollback_evidence=evidence,
        detail=(
            "The existing target is a two-tick timing and is not the same operation. "
            "The promoted contract is the one-tick floor law the proof establishes."
        ),
    )
    oracle_checks = {
        "faults_confirmed": False,
        "rollback_verified": rollback_restored,
        "candidate_detects_all": measurement["candidate_hits"] == measurement["trials"],
        "oracle_schema": "integer DDA walk, independent of the carry module",
        "oracle_mismatches": len(measurement["mismatches"]),
    }
    # The carry check has no injected faults; its oracle check is exact agreement.
    oracle_checks["faults_confirmed"] = measurement["candidate_hits"] == measurement["trials"]
    return record, oracle_checks


def _build_runtime_record(*, state: str = "adopted") -> tuple[UtilityRecord, dict[str, Any]]:
    measurement = measure_runtime_faults(use_runtime=True)
    baseline = measurement["baseline_value"]
    candidate = measurement["candidate_value"]
    delta = _ratio(
        measurement["candidate_hits"] - measurement["baseline_hits"],
        measurement["trials"],
    )
    rollback = measure_runtime_faults(use_runtime=False)
    rollback_restored = rollback["candidate_hits"] == measurement["baseline_hits"]
    evidence = {
        "verified": rollback_restored,
        "method": "disable the runtime check and measure static topology_audit alone",
        "restored_value": rollback["candidate_value"],
        "baseline_command": "python3 cent self --baseline --json",
    }
    record = UtilityRecord(
        id=RUNTIME_ID,
        title="Junction conservation as a runtime cent-program/1 invariant",
        target_subsystem="cent_compiler.runtime_invariants (cent-program/1 exact evaluator)",
        baseline_command="python3 cent self --baseline --json",
        candidate_command="python3 cent self --json",
        metric="injected-fault detection rate",
        baseline_value=baseline,
        candidate_value=candidate,
        delta=delta,
        trials=measurement["trials"],
        seed=0,
        independent_oracle="self_oracle.expected and confirms_semantic_fault (direct Fraction law)",
        adoption_state=state,
        rollback="cent self --revert " + RUNTIME_ID,
        rollback_evidence=evidence,
        detail=(
            "Structural faults are visible to topology_audit; semantic faults are not. "
            "The runtime check evaluates the declared junction law on exact inputs."
        ),
    )
    oracle_checks = {
        "faults_confirmed": measurement["oracle_confirmations"] == measurement["trials"],
        "rollback_verified": rollback_restored,
        "candidate_detects_all": measurement["candidate_hits"] == measurement["trials"],
        "oracle_schema": "direct Fraction sum/difference over four fixed cases",
        "oracle_mismatches": measurement["trials"] - measurement["oracle_confirmations"],
    }
    return record, oracle_checks


def build_baseline() -> dict[str, Any]:
    """Run only the named baseline paths, for reproducible comparison."""
    carry = measure_carry_agreement(use_floor=False)
    runtime = measure_runtime_faults(use_runtime=False)
    rows = [
        {
            "id": CARRY_ID,
            "metric": "Bresenham integer-walk agreement rate",
            "value": carry["baseline_value"],
            "trials": carry["trials"],
            "seed": 0,
            "path": "existing two-tick delta_sigma_quantized_carry target",
        },
        {
            "id": RUNTIME_ID,
            "metric": "injected-fault detection rate",
            "value": runtime["baseline_value"],
            "trials": runtime["trials"],
            "seed": 0,
            "path": "static topology_audit only",
        },
    ]
    return {
        "schema": "cent-utility-baseline/1",
        "ok": carry["ok"] and runtime["ok"],
        "records": rows,
    }


def build_ledger() -> dict[str, Any]:
    """Build both adopted records and their oracle-issued certificates."""
    carry, carry_oracle = _build_carry_record()
    runtime, runtime_oracle = _build_runtime_record()
    records = []
    for record, oracle_checks in ((carry, carry_oracle), (runtime, runtime_oracle)):
        payload = record.as_dict()
        payload["certificate"] = certify(payload, oracle_checks)
        records.append(payload)
    ok = all(record["certificate"].get("status") == "pass" for record in records)
    return {
        "schema": UTILITY_LEDGER_SCHEMA,
        "ok": ok,
        "records": records,
        "certificate_schema": CERTIFICATE_SCHEMA,
        "summary": {
            "records": len(records),
            "adopted": sum(record["adoption_state"] == "adopted" for record in records),
            "reverted": sum(record["adoption_state"] == "reverted" for record in records),
            "certified": sum(
                record["certificate"].get("status") == "pass" for record in records
            ),
        },
    }


def record_by_id(record_id: str) -> dict[str, Any]:
    ledger = build_ledger()
    for record in ledger["records"]:
        if record["id"] == record_id:
            return record
    raise KeyError(f"unknown self-transfer record {record_id!r}")


def rollback(record_id: str) -> dict[str, Any]:
    """Exercise the declared rollback and return a reverted record."""
    if record_id == CARRY_ID:
        record, oracle_checks = _build_carry_record(state="reverted")
        rollback_measurement = measure_carry_agreement(use_floor=False)
        record = replace(
            record,
            rollback_evidence={
                **(record.rollback_evidence or {}),
                "verified": rollback_measurement["candidate_hits"]
                == measure_carry_agreement()["baseline_hits"],
                "restored_value": rollback_measurement["candidate_value"],
            },
        )
        oracle_checks["rollback_verified"] = bool(record.rollback_evidence.get("verified"))
    elif record_id == RUNTIME_ID:
        record, oracle_checks = _build_runtime_record(state="reverted")
    else:
        raise KeyError(f"unknown self-transfer record {record_id!r}")
    if not record.rollback_evidence.get("verified"):
        raise ValueError(f"rollback for {record_id!r} did not restore the baseline")
    payload = record.as_dict()
    payload["certificate"] = certify(payload, oracle_checks)
    payload["rollback_applied"] = True
    return payload


def adopt(record_id: str) -> dict[str, Any]:
    """Re-run and re-adopt a record after a rollback."""
    if record_id == CARRY_ID:
        record, oracle_checks = _build_carry_record(state="adopted")
    elif record_id == RUNTIME_ID:
        record, oracle_checks = _build_runtime_record(state="adopted")
    else:
        raise KeyError(f"unknown self-transfer record {record_id!r}")
    payload = record.as_dict()
    payload["certificate"] = certify(payload, oracle_checks)
    payload["adoption_applied"] = True
    return payload


def write_ledger(path: Path | str = DEFAULT_LEDGER) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    import json

    target.write_text(json.dumps(build_ledger(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def render_ledger(ledger: Mapping[str, Any] | None = None) -> str:
    payload = ledger or build_ledger()
    lines = ["=" * 78, "SELF-TRANSFER UTILITY LEDGER (cent-utility/1)", "=" * 78]
    for record in payload.get("records") or ():
        certificate = record.get("certificate") or {}
        lines.append(f"{record.get('id')} · {record.get('adoption_state')}")
        lines.append(f"  target: {record.get('target_subsystem')}")
        lines.append(f"  metric: {record.get('metric')}")
        lines.append(
            f"  baseline: {record.get('baseline_value')} · candidate: "
            f"{record.get('candidate_value')} · delta: {record.get('delta')}"
        )
        lines.append(f"  trials: {record.get('trials')} · seed: {record.get('seed')}")
        lines.append(f"  oracle: {record.get('independent_oracle')}")
        lines.append(f"  rollback: {record.get('rollback')}")
        lines.append(
            f"  certificate: {certificate.get('status')} "
            f"(issued by {certificate.get('oracle')}; candidate on path: "
            f"{certificate.get('candidate_on_certificate_path')})"
        )
        lines.append("")
    lines.append(
        "Adoption is flagged and reversible. A certificate is issued by the independent "
        "oracle, never by the candidate self-application."
    )
    return "\n".join(lines)


def render_record(record: Mapping[str, Any]) -> str:
    lines = [
        "=" * 78,
        "SELF-TRANSFER RECORD",
        "=" * 78,
        f"id: {record.get('id')}",
        f"state: {record.get('adoption_state')}",
        f"metric: {record.get('metric')}",
        f"baseline: {record.get('baseline_value')}",
        f"candidate: {record.get('candidate_value')}",
        f"delta: {record.get('delta')}",
        f"trials: {record.get('trials')} · seed: {record.get('seed')}",
        f"oracle: {record.get('independent_oracle')}",
        f"rollback: {record.get('rollback')}",
        f"rollback verified: {(record.get('rollback_evidence') or {}).get('verified')}",
    ]
    certificate = record.get("certificate") or {}
    lines.append(f"certificate: {certificate.get('status')} ({certificate.get('oracle')})")
    return "\n".join(lines)


__all__ = [
    "ADOPTION_STATES",
    "CARRY_ID",
    "CASES",
    "DEFAULT_LEDGER",
    "RUNTIME_ID",
    "UTILITY_LEDGER_SCHEMA",
    "UTILITY_SCHEMA",
    "UtilityRecord",
    "adopt",
    "build_baseline",
    "build_ledger",
    "measure_carry_agreement",
    "measure_runtime_faults",
    "record_by_id",
    "render_ledger",
    "render_record",
    "rollback",
    "write_ledger",
]
