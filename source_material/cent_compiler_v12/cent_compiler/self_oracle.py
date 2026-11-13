"""Independent oracle for the D4 self-transfer utility records.

R5 requires an adopted analogy to be paired with an independent oracle, and
certificates to be issued by that oracle rather than by the candidate code.
This module deliberately does not import ``runtime_invariants`` or
``self_target``.  It recomputes the declared law directly with ``Fraction`` and
uses the public evaluator only to execute a mutated program for fault
confirmation.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Iterable, Mapping

from .evaluator import run_program
from .exact import CentError

ORACLE_SCHEMA = "cent-utility-oracle/1"
CERTIFICATE_SCHEMA = "cent-utility-certificate/1"


def expected(operation: str, a: Fraction, b: Fraction) -> Fraction:
    """Independent closed-form expectation for a declared junction law."""
    if operation == "sum":
        return Fraction(a) + Fraction(b)
    if operation == "difference":
        return Fraction(a) - Fraction(b)
    raise ValueError(f"oracle has no law for operation {operation!r}")


def line_walk(dx: int, dy: int) -> tuple[int, ...]:
    """Independent integer Bresenham/DDA walk (no carry module import)."""
    return tuple(((n + 1) * dy) // dx - (n * dy) // dx for n in range(dx))


def confirms_semantic_fault(
    original: Any,
    mutant: Any,
    cases: Iterable[Mapping[str, Any]],
) -> bool:
    """Whether a mutated program changes the original declared law on a case."""
    for item in cases:
        a = Fraction(item["a"])
        b = Fraction(item["b"])
        want = expected(original.operation, a, b)
        try:
            values = run_program(mutant.program, [{"a": a, "b": b}])[0]
            got = Fraction(values["total"])
        except (CentError, KeyError, TypeError, ValueError, ZeroDivisionError):
            return True
        if got != want:
            return True
    return False


def _parse_ratio(value: str) -> Fraction:
    if not isinstance(value, str) or "/" not in value:
        raise ValueError(f"utility value must be an 'a/b' ratio, got {value!r}")
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"invalid utility ratio {value!r}: {exc}") from exc


def certify(record: Mapping[str, Any], oracle_checks: Mapping[str, Any]) -> dict[str, Any]:
    """Issue ``cent-utility-certificate/1`` from independently checked facts."""
    failures: list[str] = []
    baseline = _parse_ratio(str(record.get("baseline_value", "")))
    candidate = _parse_ratio(str(record.get("candidate_value", "")))
    delta = _parse_ratio(str(record.get("delta", "")))
    if candidate - baseline != delta:
        failures.append("declared delta is not candidate minus baseline")
    if delta <= 0:
        failures.append("utility delta is not positive")
    if not record.get("independent_oracle"):
        failures.append("utility record has no independent oracle")
    if not record.get("rollback"):
        failures.append("utility record has no rollback")
    if record.get("adoption_state") not in {"adopted", "reverted", "proposed"}:
        failures.append("unknown adoption state")
    if not oracle_checks.get("faults_confirmed"):
        failures.append("oracle did not confirm every injected fault")
    if not oracle_checks.get("rollback_verified"):
        failures.append("oracle did not verify rollback restores the baseline")
    if not oracle_checks.get("candidate_detects_all"):
        failures.append("candidate does not detect every confirmed fault")
    return {
        "schema": CERTIFICATE_SCHEMA,
        "status": "pass" if not failures else "gap",
        "metric": record.get("metric"),
        "baseline_value": record.get("baseline_value"),
        "candidate_value": record.get("candidate_value"),
        "delta": record.get("delta"),
        "independent_oracle": record.get("independent_oracle"),
        "oracle": ORACLE_SCHEMA,
        "candidate_on_certificate_path": False,
        "checks": dict(oracle_checks),
        "failures": failures,
    }


__all__ = [
    "CERTIFICATE_SCHEMA",
    "ORACLE_SCHEMA",
    "certify",
    "confirms_semantic_fault",
    "expected",
    "line_walk",
]
