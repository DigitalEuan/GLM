"""Runtime invariants for exact ``cent-program/1`` routes.

The static topology audit checks that a route is well formed.  It cannot see a
well-formed program that computes the wrong law.  This module adds the runtime
half: evaluate the declared program over fixed exact inputs and compare its
output with the route's declared algebraic invariant.

The checker is deliberately small and independent of the target adapters.  It
is used by ``cent self`` as the candidate against the static
``topology_audit`` baseline; ``self_oracle`` independently confirms that each
injected fault really changes the declared law.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Iterable, Mapping

from .evaluator import run_program
from .exact import CentError, ErrorCode

SCHEMA = "cent-runtime-invariants/1"
CHECK_SCHEMA = "cent-runtime-invariant-check/1"


@dataclass(frozen=True)
class RuntimeCheck:
    """One exact input pair and its declared result."""

    name: str
    a: Fraction
    b: Fraction
    expected: Fraction
    observed: Fraction
    passed: bool
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "a": {"num": self.a.numerator, "den": self.a.denominator},
            "b": {"num": self.b.numerator, "den": self.b.denominator},
            "expected": {"num": self.expected.numerator, "den": self.expected.denominator},
            "observed": {"num": self.observed.numerator, "den": self.observed.denominator},
            "passed": self.passed,
            "detail": self.detail,
        }


def expected_value(operation: str, a: Fraction, b: Fraction) -> Fraction:
    """The declared junction law for the route operation."""
    if operation == "sum":
        return a + b
    if operation == "difference":
        return a - b
    raise CentError(
        ErrorCode.UNSUPPORTED,
        f"runtime invariant has no law for operation {operation!r}",
    )


def check_program(
    program: Any,
    operation: str,
    inputs: Iterable[Mapping[str, Any]],
    *,
    output: str = "total",
) -> dict[str, Any]:
    """Evaluate a program over ``inputs`` and compare to the declared law."""
    checks: list[RuntimeCheck] = []
    for index, item in enumerate(inputs):
        name = str(item.get("name", f"vector-{index + 1}"))
        try:
            a = Fraction(item["a"])
            b = Fraction(item["b"])
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            checks.append(
                RuntimeCheck(name, Fraction(0), Fraction(0), Fraction(0), Fraction(0), False, str(exc))
            )
            continue
        expected = expected_value(operation, a, b)
        try:
            values = run_program(program, [{"a": a, "b": b}])[0]
            observed = Fraction(values[output])
            passed = observed == expected
            detail = "observed output equals the declared junction law"
        except (CentError, KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            observed = Fraction(0)
            passed = False
            detail = f"program did not yield a comparable {output!r}: {exc}"
        checks.append(RuntimeCheck(name, a, b, expected, observed, passed, detail))
    failures = [check.name for check in checks if not check.passed]
    return {
        "schema": CHECK_SCHEMA,
        "kind": "runtime",
        "operation": operation,
        "output": output,
        "checks": [check.as_dict() for check in checks],
        "checked": len(checks),
        "passed": len(checks) - len(failures),
        "failures": failures,
        "ok": not failures and bool(checks),
    }


def check_route(route: Any, inputs: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Run the runtime invariant check on a route-like object."""
    return check_program(
        getattr(route, "program"),
        getattr(route, "operation"),
        inputs,
        output="total",
    )


__all__ = ["CHECK_SCHEMA", "SCHEMA", "RuntimeCheck", "check_program", "check_route", "expected_value"]
