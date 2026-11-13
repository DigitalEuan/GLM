"""The declared one-tick ``quantized_carry_floor`` contract.

This module promotes the already checked Bresenham/one-tick delta-sigma
correspondence in ``docs/evidence/bresenham/check.py`` into a compiler-owned
operation contract.  The existing ``quantized_carry`` target is a two-tick
first-order error-feedback timing; it is a different operation, not a bug in
this one.  The declared law here is exactly the one the proof satisfies:

    q_n = floor(y_n) - floor(y_{n-1}),   y_n = (n + 1) * x

for rational ``0 <= x < 1``.  No device, clock, or fabricated timing is
claimed: the timing field says one tick of the exact model.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from .exact import CentError, ErrorCode, q

SCHEMA = "cent-quantized-carry-floor/1"
CONTRACT_SCHEMA = "cent-operation-contract/1"

CONTRACT: dict[str, Any] = {
    "schema": CONTRACT_SCHEMA,
    "id": "quantized_carry_floor",
    "name": "one-tick floor carry",
    "law": "q_n = floor((n + 1) * x) - floor(n * x)",
    "state": "r_n = frac(n * x), consumed by the next floor",
    "timing": "one tick per output code; state is updated before the code is read",
    "domain": "exact rational 0 <= x <= 1",
    "target": "exact arithmetic reference; no device or clock claim",
    "provenance": "docs/evidence/bresenham/check.py",
    "evidence": "exact equivalence checked for 1 <= dx <= 32, 0 <= dy <= dx",
}


def _as_fraction(value: Any, name: str) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        raise CentError(ErrorCode.INVALID_INPUT, f"{name} must be a rational, not boolean")
    try:
        return q(value, name)
    except CentError:
        raise
    except Exception as exc:  # pragma: no cover - q normally wraps this
        raise CentError(ErrorCode.INVALID_INPUT, f"{name} must be an exact rational: {exc}") from exc


def floor_carry_sequence(input_value: Any, samples: int) -> tuple[int, ...]:
    """Return the exact one-tick floor-carry code for ``input_value``."""
    if isinstance(samples, bool) or not isinstance(samples, int) or samples < 1:
        raise CentError(ErrorCode.INVALID_INPUT, "samples must be a positive integer")
    x = _as_fraction(input_value, "input")
    if x < 0 or x > 1:
        raise CentError(ErrorCode.INVALID_INPUT, "quantized_carry_floor input must satisfy 0 <= x <= 1")
    residual = Fraction(0)
    code: list[int] = []
    for _ in range(samples):
        residual += x
        level = residual.numerator // residual.denominator
        code.append(level)
        residual -= level
    return tuple(code)


def line_walk(dx: int, dy: int) -> tuple[int, ...]:
    """Integer DDA/Bresenham walk for a line of ``dx`` steps and ``dy`` rise."""
    if isinstance(dx, bool) or isinstance(dy, bool) or dx < 1 or dy < 0 or dy > dx:
        raise CentError(ErrorCode.INVALID_INPUT, "line_walk requires integers 1 <= dx and 0 <= dy <= dx")
    return tuple(((n + 1) * dy) // dx - (n * dy) // dx for n in range(dx))


def check_contract(max_dx: int = 16) -> dict[str, Any]:
    """Check the declared contract against the independent integer walk."""
    trials = 0
    failures: list[dict[str, Any]] = []
    for dx in range(1, max_dx + 1):
        for dy in range(dx + 1):
            trials += 1
            expected = line_walk(dx, dy)
            observed = floor_carry_sequence(Fraction(dy, dx), dx)
            if observed != expected:
                failures.append(
                    {
                        "dx": dx,
                        "dy": dy,
                        "expected": list(expected),
                        "observed": list(observed),
                    }
                )
    return {
        "schema": "cent-quantized-carry-floor-check/1",
        "contract": CONTRACT["id"],
        "trials": trials,
        "passed": trials - len(failures),
        "failed": len(failures),
        "ok": not failures,
        "failures": failures[:8],
    }


def render_contract() -> str:
    lines = ["=" * 78, "DECLARED OPERATION CONTRACT", "=" * 78]
    for key in ("id", "name", "law", "state", "timing", "domain", "target", "provenance"):
        lines.append(f"{key}: {CONTRACT[key]}")
    return "\n".join(lines)


def contract_json() -> dict[str, Any]:
    return dict(CONTRACT)


__all__ = [
    "CONTRACT",
    "CONTRACT_SCHEMA",
    "SCHEMA",
    "check_contract",
    "contract_json",
    "floor_carry_sequence",
    "line_walk",
    "render_contract",
]
