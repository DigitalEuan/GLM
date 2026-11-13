"""The declared ``glm-reference`` software target.

This module is an adapter experiment, not a GLM integration.  It defines an
exact-rational, pure-Python reference contract for the ``quantized_carry``,
``sum``, ``difference`` and ``sqrt`` operations.  It executes the first-order
error-feedback mechanism, the KCL exact sum/difference mechanisms, the
normalized fluid-continuity sum and the log-domain square root against fixed
vectors.  There is no model call, no learned parameter, no external GLM
latency or bit-budget claim, and no measured GLM performance result here.

The target adapter is intentionally independent of ``cent_compiler.assembly``:
the validator compares the two implementations rather than having one call the
other.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Callable, Mapping

from ..exact import Q, q, q_to_json, sign as exact_sign
from ..interval import Interval, exp_q, log_q, sqrt_q
from ..transfer import TargetProfile

TARGET_ID = "glm-reference"
ADAPTER_SCHEMA = "cent-glm-adapter/1"
VECTOR_SCHEMA = "cent-glm-vector/1"


def _fraction(value: Any, name: str) -> Q:
    """Coerce an exact rational, accepting the project's ``a/b`` spelling."""
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an exact rational, not boolean")
    if isinstance(value, str) and "/" in value:
        try:
            return Fraction(value.strip())
        except (ValueError, ZeroDivisionError) as exc:
            raise ValueError(f"{name} is not an exact fraction: {value!r}") from exc
    try:
        return q(value, name)
    except Exception as exc:  # q raises a structured CentError
        raise ValueError(f"{name} must be an exact rational: {exc}") from exc


def _settings(
    *,
    samples: Any,
    quantum: Any,
    full_scale: Any,
    integrator_limit: Any,
) -> tuple[int, Q, Q, Q]:
    if isinstance(samples, bool) or not isinstance(samples, int):
        raise ValueError("samples must be an integer")
    if samples < 1:
        raise ValueError("samples must be at least one")
    quantum_q = _fraction(quantum, "quantum")
    full_scale_q = _fraction(full_scale, "full_scale")
    limit_q = _fraction(integrator_limit, "integrator_limit")
    if quantum_q <= 0:
        raise ValueError("quantum must be positive")
    if full_scale_q <= 0:
        raise ValueError("full_scale must be positive")
    if quantum_q > full_scale_q:
        raise ValueError("quantum cannot exceed full_scale")
    if (full_scale_q / quantum_q).denominator != 1:
        raise ValueError("full_scale must be an integer multiple of quantum")
    if limit_q <= 0:
        raise ValueError("integrator_limit must be positive")
    return samples, quantum_q, full_scale_q, limit_q


def _quantize(value: Q, quantum: Q) -> Q:
    """Nearest declared level, with ties away from zero (same declared law)."""
    magnitude = abs(value) / quantum
    steps = (magnitude + Fraction(1, 2)).__floor__()
    return Fraction(steps) * quantum * (1 if value >= 0 else -1)


def _clamp(value: Q, lo: Q, hi: Q) -> Q:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def _json_value(value: Any) -> Any:
    if isinstance(value, Fraction):
        return q_to_json(value)
    if isinstance(value, Interval):
        return {
            "lo": q_to_json(value.lo),
            "hi": q_to_json(value.hi),
            "width": q_to_json(value.width),
        }
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


@dataclass(frozen=True)
class TargetRun:
    """One exact execution of a target adapter."""

    adapter: str
    x: Q
    samples: int
    quantum: Q
    full_scale: Q
    code: tuple[int, ...]
    mean: Q
    error: Q
    peak_state: Q
    bounded: bool
    passed: bool
    trace: tuple[Mapping[str, Any], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "adapter": self.adapter,
            "input": q_to_json(self.x),
            "samples": self.samples,
            "quantum": q_to_json(self.quantum),
            "full_scale": q_to_json(self.full_scale),
            "code": list(self.code),
            "mean": q_to_json(self.mean),
            "error": q_to_json(self.error),
            "peak_state": q_to_json(self.peak_state),
            "bounded": self.bounded,
            "passed": self.passed,
            "trace": [_json_value(item) for item in self.trace],
        }


@dataclass(frozen=True)
class SumRun:
    """One exact execution of a KCL target adapter."""

    adapter: str
    a: Q
    b: Q
    result: Q
    expected: Q
    passed: bool
    operation: str = "sum"

    def as_dict(self) -> dict[str, Any]:
        return {
            "adapter": self.adapter,
            "operation": self.operation,
            "a": q_to_json(self.a),
            "b": q_to_json(self.b),
            "result": q_to_json(self.result),
            "expected": q_to_json(self.expected),
            "passed": self.passed,
        }


@dataclass(frozen=True)
class SignRun:
    """One exact execution of the three-level sign reference adapter."""

    adapter: str
    x: Q
    result: int
    passed: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "adapter": self.adapter,
            "input": q_to_json(self.x),
            "result": self.result,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class SignVector:
    """A fixed sign vector with its expected exact result."""

    id: str
    x: Q
    expected: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": VECTOR_SCHEMA,
            "id": self.id,
            "x": q_to_json(self.x),
            "expected": self.expected,
        }


@dataclass(frozen=True)
class GlmVector:
    """A fixed target test vector with its expected source output."""

    id: str
    x: Q
    samples: int
    quantum: Q
    full_scale: Q
    integrator_limit: Q
    expected_code: tuple[int, ...]
    expected_mean: Q

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": VECTOR_SCHEMA,
            "id": self.id,
            "input": q_to_json(self.x),
            "samples": self.samples,
            "quantum": q_to_json(self.quantum),
            "full_scale": q_to_json(self.full_scale),
            "integrator_limit": q_to_json(self.integrator_limit),
            "expected_code": list(self.expected_code),
            "expected_mean": q_to_json(self.expected_mean),
        }


@dataclass(frozen=True)
class KclVector:
    """A fixed exact-sum target vector."""

    id: str
    a: Q
    b: Q
    expected: Q

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": VECTOR_SCHEMA,
            "id": self.id,
            "a": q_to_json(self.a),
            "b": q_to_json(self.b),
            "expected": q_to_json(self.expected),
        }


@dataclass(frozen=True)
class FluidVector:
    """A fixed normalized-flow vector for the fluid-continuity sum."""

    id: str
    a: Q
    b: Q
    expected: Q

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": VECTOR_SCHEMA,
            "id": self.id,
            "a": q_to_json(self.a),
            "b": q_to_json(self.b),
            "expected": q_to_json(self.expected),
        }


@dataclass(frozen=True)
class SqrtVector:
    """A fixed positive-input vector for the log-domain square root."""

    id: str
    x: Q
    precision: int
    tolerance: Q

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": VECTOR_SCHEMA,
            "id": self.id,
            "x": q_to_json(self.x),
            "precision": self.precision,
            "tolerance": q_to_json(self.tolerance),
        }


@dataclass(frozen=True)
class ArithmeticVector:
    """A fixed log-domain arithmetic vector."""

    id: str
    operation: str
    x: Q = Fraction(0)
    a: Q = Fraction(0)
    b: Q = Fraction(1)
    c: Q = Fraction(1)
    precision: int = 20
    tolerance: Q = Fraction(1, 10000)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": VECTOR_SCHEMA,
            "id": self.id,
            "operation": self.operation,
            "x": q_to_json(self.x),
            "a": q_to_json(self.a),
            "b": q_to_json(self.b),
            "c": q_to_json(self.c),
            "precision": self.precision,
            "tolerance": q_to_json(self.tolerance),
        }


@dataclass(frozen=True)
class ArithmeticTargetRun:
    """One target-side log-domain arithmetic enclosure."""

    adapter: str
    operation: str
    inputs: Mapping[str, Q]
    precision: int
    tolerance: Q
    result: Interval
    checker: Interval
    passed: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "adapter": self.adapter,
            "operation": self.operation,
            "inputs": {name: q_to_json(value) for name, value in self.inputs.items()},
            "precision": self.precision,
            "tolerance": q_to_json(self.tolerance),
            "result": _json_value(self.result),
            "checker": _json_value(self.checker),
            "width": q_to_json(self.result.width),
            "passed": self.passed,
        }


@dataclass(frozen=True)
class SqrtTargetRun:
    """One target-side log-domain square-root enclosure."""

    adapter: str
    x: Q
    precision: int
    tolerance: Q
    ln_x: Interval
    half_ln: Interval
    root: Interval
    checker: Interval
    passed: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "adapter": self.adapter,
            "x": q_to_json(self.x),
            "precision": self.precision,
            "tolerance": q_to_json(self.tolerance),
            "ln_x": _json_value(self.ln_x),
            "half_ln": _json_value(self.half_ln),
            "root": _json_value(self.root),
            "checker": _json_value(self.checker),
            "root_width": q_to_json(self.root.width),
            "passed": self.passed,
        }


@dataclass(frozen=True)
class AdapterSpec:
    """A declared executable target adapter."""

    id: str
    operation: str
    mechanism: str
    entrypoint: str
    function: Callable[..., Any]
    description: str
    vectors: tuple[GlmVector | KclVector | FluidVector | SqrtVector | ArithmeticVector, ...]
    kind: str = "quantized_carry"

    @property
    def path(self) -> str:
        return "cent_compiler/targets/glm.py"

    @property
    def invocation(self) -> str:
        if self.operation in {"sum", "difference"}:
            return f"{self.entrypoint}(a, b)"
        if self.operation in {"sqrt", "exp", "log"}:
            return f"{self.entrypoint}(x, precision=..., tolerance=...)"
        if self.operation in {"mult", "div"}:
            return f"{self.entrypoint}(a, b, precision=..., tolerance=...)"
        if self.operation == "sign":
            return f"{self.entrypoint}(x)"
        return (
            f"{self.entrypoint}(x, samples=..., quantum=..., "
            "full_scale=..., integrator_limit=...)"
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": ADAPTER_SCHEMA,
            "id": self.id,
            "operation": self.operation,
            "mechanism": self.mechanism,
            "target": TARGET_ID,
            "kind": "python-callable",
            "operation_kind": self.kind,
            "path": self.path,
            "entrypoint": self.entrypoint,
            "invocation": self.invocation,
            "precision": "exact rational; no binary floats",
            "description": self.description,
            "test_vectors": [vector.id for vector in self.vectors],
        }


def delta_sigma_quantized_carry(
    x: Any,
    *,
    samples: int = 12,
    quantum: Any = Fraction(1),
    full_scale: Any = Fraction(1),
    integrator_limit: Any = Fraction(8),
) -> TargetRun:
    """Run the first-order error-feedback carry in the reference target.

    The loop is the declared transfer mapping: an exact accumulator, a
    nearest-level quantizer with ties away from zero, and a one-sample feedback
    delay.  It is deliberately a target-side implementation, not a call into the
    physical route being compared.
    """
    samples_i, quantum_q, full_scale_q, limit_q = _settings(
        samples=samples,
        quantum=quantum,
        full_scale=full_scale,
        integrator_limit=integrator_limit,
    )
    x_q = _fraction(x, "x")
    if not (Fraction(0) <= x_q <= full_scale_q):
        raise ValueError(f"x must be in [0, {full_scale_q}], got {x_q}")

    state = Fraction(0)
    # The declared route has a feedback edge that reads the previous delay
    # output.  Its effective history is two ticks; preserve that exact law.
    feedback_history = [Fraction(0), Fraction(0)]
    total = Fraction(0)
    peak = Fraction(0)
    code: list[int] = []
    trace: list[Mapping[str, Any]] = []

    for tick in range(1, samples_i + 1):
        feedback = feedback_history.pop(0)
        error = x_q - feedback
        state += error
        peak = max(peak, abs(state))
        raw_level = _quantize(state, quantum_q)
        level = _clamp(raw_level, Fraction(0), full_scale_q)
        level_code = int(level / quantum_q)
        code.append(level_code)
        total += level
        trace.append(
            {
                "tick": tick,
                "input": x_q,
                "error": error,
                "state": state,
                "raw_level": raw_level,
                "level": level,
                "feedback": feedback,
            }
        )
        feedback_history.append(level)

    mean = total / samples_i
    error = mean - x_q
    bounded = peak <= limit_q
    return TargetRun(
        adapter="delta-sigma-error-feedback",
        x=x_q,
        samples=samples_i,
        quantum=quantum_q,
        full_scale=full_scale_q,
        code=tuple(code),
        mean=mean,
        error=error,
        peak_state=peak,
        bounded=bounded,
        passed=bounded and abs(error) <= quantum_q,
        trace=tuple(trace),
    )


def uniform_quantizer_carry(
    x: Any,
    *,
    samples: int = 12,
    quantum: Any = Fraction(1),
    full_scale: Any = Fraction(1),
) -> TargetRun:
    """Plain per-sample uniform quantizer used as the declared baseline.

    This is stateless: every sample is quantized independently.  It is not a
    delta-sigma implementation and is never eligible to be promoted as one.
    """
    samples_i, quantum_q, full_scale_q, _limit_q = _settings(
        samples=samples,
        quantum=quantum,
        full_scale=full_scale,
        integrator_limit=Fraction(8),
    )
    x_q = _fraction(x, "x")
    if not (Fraction(0) <= x_q <= full_scale_q):
        raise ValueError(f"x must be in [0, {full_scale_q}], got {x_q}")
    level = _clamp(_quantize(x_q, quantum_q), Fraction(0), full_scale_q)
    code = tuple(int(level / quantum_q) for _ in range(samples_i))
    mean = level
    error = mean - x_q
    return TargetRun(
        adapter="uniform-quantizer-baseline",
        x=x_q,
        samples=samples_i,
        quantum=quantum_q,
        full_scale=full_scale_q,
        code=code,
        mean=mean,
        error=error,
        peak_state=Fraction(0),
        bounded=True,
        passed=abs(error) <= quantum_q,
        trace=(),
    )


def exact_kcl_sum(a: Any, b: Any) -> SumRun:
    """Execute the target-side exact KCL sum adapter.

    This is a target implementation of the declared junction operation, not a
    call into ``assembly.kcl_sum_route``; the validator compares both results.
    """
    a_q = _fraction(a, "a")
    b_q = _fraction(b, "b")
    result = a_q + b_q
    return SumRun(
        adapter="kcl-conservation",
        a=a_q,
        b=b_q,
        result=result,
        expected=result,
        passed=True,
        operation="sum",
    )


def exact_fluid_sum(a: Any, b: Any) -> SumRun:
    """Execute the target-side normalized fluid-continuity sum adapter.

    The declared law is ``q_total = q_a + q_b`` on normalized exact flows.  It
    does not call ``assembly.fluid_sum_route``; the validator compares the two
    independent implementations.  Pressure/flow scaling, leakage, junction loss
    and compressibility remain outside this normalized model.
    """
    a_q = _fraction(a, "a")
    b_q = _fraction(b, "b")
    result = a_q + b_q
    return SumRun(
        adapter="fluid-continuity",
        a=a_q,
        b=b_q,
        result=result,
        expected=result,
        passed=True,
        operation="sum",
    )


def exact_opamp_sum(a: Any, b: Any) -> SumRun:
    """Execute the target-side ideal op-amp summing adapter.

    The declared block is a matched non-inverting summing amplifier with 1/2
    attenuation per input and closed-loop gain 2, so the normalized result is
    ``a + b``. It does not call ``assembly.opamp_sum_route``; the validator
    compares the two independent implementations. Resistor mismatch, finite
    gain/bandwidth, offset and loading remain outside this ideal block model.
    """
    a_q = _fraction(a, "a")
    b_q = _fraction(b, "b")
    result = a_q + b_q
    return SumRun(
        adapter="opamp-summing",
        a=a_q,
        b=b_q,
        result=result,
        expected=result,
        passed=True,
        operation="sum",
    )


def exact_opamp_difference(a: Any, b: Any) -> SumRun:
    """Execute the target-side ideal op-amp difference adapter.

    The declared block is an ideal inverting buffer on the second input followed
    by the matched summing amplifier, so the normalized result is ``a - b``. It
    does not call ``assembly.opamp_sum_route(operation="difference")``; the
    validator compares the two independent implementations.
    """
    a_q = _fraction(a, "a")
    b_q = _fraction(b, "b")
    result = a_q - b_q
    return SumRun(
        adapter="opamp-summing-difference",
        a=a_q,
        b=b_q,
        result=result,
        expected=result,
        passed=True,
        operation="difference",
    )


def exact_fluid_difference(a: Any, b: Any) -> SumRun:
    """Execute the target-side normalized fluid-continuity difference adapter.

    Subtraction is the declared reversed-port negation of the second input
    followed by the exact flow-conservation junction.  It does not call
    ``assembly.fluid_sum_route(operation="difference")``; the validator compares
    the two independent implementations.  Pressure/flow scaling, leakage,
    compressibility and junction loss remain outside this normalized model.
    """
    a_q = _fraction(a, "a")
    b_q = _fraction(b, "b")
    result = a_q - b_q
    return SumRun(
        adapter="fluid-continuity-difference",
        a=a_q,
        b=b_q,
        result=result,
        expected=result,
        passed=True,
        operation="difference",
    )


def exact_kcl_difference(a: Any, b: Any) -> SumRun:
    """Execute the target-side exact KCL difference adapter.

    Subtraction is the declared negation of the second input followed by an
    exact sum, matching the source route without calling it.
    """
    a_q = _fraction(a, "a")
    b_q = _fraction(b, "b")
    result = a_q - b_q
    return SumRun(
        adapter="kcl-conservation-difference",
        a=a_q,
        b=b_q,
        result=result,
        expected=result,
        passed=True,
        operation="difference",
    )


def log_domain_sqrt(
    x: Any,
    *,
    precision: int = 20,
    tolerance: Any = Fraction(1, 10000),
) -> SqrtTargetRun:
    """Execute the target-side exact-rational log-domain square root.

    The route is ``exp((1/2) * log(x))`` using the declared interval primitives,
    not the source assembly route.  The independent ``sqrt_q`` checker is used
    only as a baseline; the returned ``passed`` flag requires both overlap and
    the declared tolerance.
    """
    if isinstance(precision, bool) or not isinstance(precision, int):
        raise ValueError("precision must be an integer")
    if not 1 <= precision <= 64:
        raise ValueError("precision must be in 1..64 bits")
    x_q = _fraction(x, "x")
    if x_q <= 0:
        raise ValueError(f"log-domain sqrt input must be positive, got {x_q}")
    tolerance_q = _fraction(tolerance, "tolerance")
    if tolerance_q <= 0:
        raise ValueError("tolerance must be positive")
    ln_x = log_q(x_q, precision)
    half_ln = Interval(
        ln_x.lo * Fraction(1, 2), ln_x.hi * Fraction(1, 2)
    )
    root = exp_q(half_ln.lo, precision) | exp_q(half_ln.hi, precision)
    checker = sqrt_q(x_q, precision)
    overlap = max(root.lo, checker.lo) <= min(root.hi, checker.hi)
    passed = overlap and root.width <= tolerance_q
    return SqrtTargetRun(
        adapter="log-domain-sqrt",
        x=x_q,
        precision=precision,
        tolerance=tolerance_q,
        ln_x=ln_x,
        half_ln=half_ln,
        root=root,
        checker=checker,
        passed=passed,
    )


def _precision(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("precision must be an integer")
    if not 1 <= value <= 64:
        raise ValueError("precision must be in 1..64 bits")
    return value


def _tolerance(value: Any) -> Q:
    tolerance_q = _fraction(value, "tolerance")
    if tolerance_q <= 0:
        raise ValueError("tolerance must be positive")
    return tolerance_q


def log_domain_exp(
    x: Any,
    *,
    precision: int = 20,
    tolerance: Any = Fraction(1, 10000),
) -> ArithmeticTargetRun:
    """Target-side certified ``exp(x)`` from the antilog junction."""
    x_q = _fraction(x, "x")
    p = _precision(precision)
    tol = _tolerance(tolerance)
    result = exp_q(x_q, p)
    checker = exp_q(x_q, min(64, p + 8))
    overlap = max(result.lo, checker.lo) <= min(result.hi, checker.hi)
    return ArithmeticTargetRun(
        adapter="log-domain-exp",
        operation="exp",
        inputs={"x": x_q},
        precision=p,
        tolerance=tol,
        result=result,
        checker=checker,
        passed=overlap and result.width <= tol,
    )


def log_domain_log(
    x: Any,
    *,
    precision: int = 20,
    tolerance: Any = Fraction(1, 10000),
) -> ArithmeticTargetRun:
    """Target-side certified ``log(x)`` from the logging junction."""
    x_q = _fraction(x, "x")
    if x_q <= 0:
        raise ValueError("log-domain log input must be positive")
    p = _precision(precision)
    tol = _tolerance(tolerance)
    result = log_q(x_q, p)
    checker = log_q(x_q, min(64, p + 8))
    overlap = max(result.lo, checker.lo) <= min(result.hi, checker.hi)
    return ArithmeticTargetRun(
        adapter="log-domain-log",
        operation="log",
        inputs={"x": x_q},
        precision=p,
        tolerance=tol,
        result=result,
        checker=checker,
        passed=overlap and result.width <= tol,
    )


def log_domain_mult(
    a: Any,
    b: Any,
    *,
    precision: int = 20,
    tolerance: Any = Fraction(1, 10000),
) -> ArithmeticTargetRun:
    """Target-side ``exp(log(a) + log(b))`` with exact product checker."""
    a_q, b_q = _fraction(a, "a"), _fraction(b, "b")
    if a_q <= 0 or b_q <= 0:
        raise ValueError("log-domain mult inputs must be positive")
    p = _precision(precision)
    tol = _tolerance(tolerance)
    ln_a = log_q(a_q, p)
    ln_b = log_q(b_q, p)
    ln_ab = ln_a + ln_b
    result = exp_q(ln_ab.lo, p) | exp_q(ln_ab.hi, p)
    checker = Interval.point(a_q * b_q)
    passed = result.contains(a_q * b_q) and result.width <= tol
    return ArithmeticTargetRun(
        adapter="log-domain-mult",
        operation="mult",
        inputs={"a": a_q, "b": b_q},
        precision=p,
        tolerance=tol,
        result=result,
        checker=checker,
        passed=passed,
    )


def log_domain_div(
    a: Any,
    b: Any,
    *,
    precision: int = 20,
    tolerance: Any = Fraction(1, 10000),
) -> ArithmeticTargetRun:
    """Target-side ``exp(log(a) - log(b))`` with exact quotient checker."""
    a_q, b_q = _fraction(a, "a"), _fraction(b, "b")
    if a_q <= 0 or b_q <= 0:
        raise ValueError("log-domain div inputs must be positive")
    p = _precision(precision)
    tol = _tolerance(tolerance)
    ln_a = log_q(a_q, p)
    ln_b = log_q(b_q, p)
    ln_ab = ln_a - ln_b
    result = exp_q(ln_ab.lo, p) | exp_q(ln_ab.hi, p)
    checker = Interval.point(a_q / b_q)
    passed = result.contains(a_q / b_q) and result.width <= tol
    return ArithmeticTargetRun(
        adapter="log-domain-div",
        operation="div",
        inputs={"a": a_q, "b": b_q},
        precision=p,
        tolerance=tol,
        result=result,
        checker=checker,
        passed=passed,
    )


def log_domain_mult_div(
    a: Any,
    b: Any,
    c: Any,
    *,
    precision: int = 20,
    tolerance: Any = Fraction(1, 10000),
) -> ArithmeticTargetRun:
    """Target-side composed ``(a*b)/c`` enclosure.

    This is one declared composition of the same two log-domain operations,
    implemented independently of the source route.  It is still a reference
    software target, not a measured junction or a composed device.
    """
    a_q, b_q, c_q = _fraction(a, "a"), _fraction(b, "b"), _fraction(c, "c")
    if a_q <= 0 or b_q <= 0 or c_q <= 0:
        raise ValueError("log-domain mult-div inputs must be positive")
    p = _precision(precision)
    tol = _tolerance(tolerance)
    ln_a = log_q(a_q, p)
    ln_b = log_q(b_q, p)
    ln_c = log_q(c_q, p)
    ln_abc = ln_a + ln_b - ln_c
    result = exp_q(ln_abc.lo, p) | exp_q(ln_abc.hi, p)
    checker = Interval.point(a_q * b_q / c_q)
    passed = result.contains(checker.lo) and result.width <= tol
    return ArithmeticTargetRun(
        adapter="log-domain-mult-div",
        operation="mult-div",
        inputs={"a": a_q, "b": b_q, "c": c_q},
        precision=p,
        tolerance=tol,
        result=result,
        checker=checker,
        passed=passed,
    )


def log_domain_div_mult(
    a: Any,
    b: Any,
    c: Any,
    *,
    precision: int = 20,
    tolerance: Any = Fraction(1, 10000),
) -> ArithmeticTargetRun:
    """Target-side composed ``(a/b)*c`` enclosure."""
    a_q, b_q, c_q = _fraction(a, "a"), _fraction(b, "b"), _fraction(c, "c")
    if a_q <= 0 or b_q <= 0 or c_q <= 0:
        raise ValueError("log-domain div-mult inputs must be positive")
    p = _precision(precision)
    tol = _tolerance(tolerance)
    ln_a = log_q(a_q, p)
    ln_b = log_q(b_q, p)
    ln_c = log_q(c_q, p)
    ln_abc = ln_a - ln_b + ln_c
    result = exp_q(ln_abc.lo, p) | exp_q(ln_abc.hi, p)
    checker = Interval.point(a_q * c_q / b_q)
    passed = result.contains(checker.lo) and result.width <= tol
    return ArithmeticTargetRun(
        adapter="log-domain-div-mult",
        operation="div-mult",
        inputs={"a": a_q, "b": b_q, "c": c_q},
        precision=p,
        tolerance=tol,
        result=result,
        checker=checker,
        passed=passed,
    )


def log_domain_mult_reciprocal(
    a: Any,
    b: Any,
    *,
    precision: int = 20,
    tolerance: Any = Fraction(1, 10000),
) -> ArithmeticTargetRun:
    """Target-side composed ``1/(a*b)`` enclosure."""
    a_q, b_q = _fraction(a, "a"), _fraction(b, "b")
    if a_q <= 0 or b_q <= 0:
        raise ValueError("log-domain mult-reciprocal inputs must be positive")
    p = _precision(precision)
    tol = _tolerance(tolerance)
    ln_a = log_q(a_q, p)
    ln_b = log_q(b_q, p)
    neg_ln_ab = -(ln_a + ln_b)
    result = exp_q(neg_ln_ab.lo, p) | exp_q(neg_ln_ab.hi, p)
    checker = Interval.point(Fraction(1) / (a_q * b_q))
    passed = result.contains(checker.lo) and result.width <= tol
    return ArithmeticTargetRun(
        adapter="log-domain-mult-reciprocal",
        operation="mult-reciprocal",
        inputs={"a": a_q, "b": b_q},
        precision=p,
        tolerance=tol,
        result=result,
        checker=checker,
        passed=passed,
    )


def log_domain_reciprocal(
    x: Any,
    *,
    precision: int = 20,
    tolerance: Any = Fraction(1, 10000),
) -> ArithmeticTargetRun:
    """Target-side ``exp(-log(x))`` with an exact reciprocal checker.

    The declared log-domain route covers positive inputs only; a negative or
    zero input is rejected rather than silently using another route.
    """
    x_q = _fraction(x, "x")
    if x_q <= 0:
        raise ValueError("log-domain reciprocal input must be positive")
    p = _precision(precision)
    tol = _tolerance(tolerance)
    ln_x = log_q(x_q, p)
    neg_ln = -ln_x
    result = exp_q(neg_ln.lo, p) | exp_q(neg_ln.hi, p)
    exact = Fraction(1) / x_q
    checker = Interval.point(exact)
    passed = result.contains(exact) and result.width <= tol
    return ArithmeticTargetRun(
        adapter="log-domain-reciprocal",
        operation="reciprocal",
        inputs={"x": x_q},
        precision=p,
        tolerance=tol,
        result=result,
        checker=checker,
        passed=passed,
    )


FIXED_VECTORS: tuple[GlmVector, ...] = (
    GlmVector(
        id="half-12",
        x=Fraction(1, 2),
        samples=12,
        quantum=Fraction(1),
        full_scale=Fraction(1),
        integrator_limit=Fraction(8),
        expected_code=(1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0),
        expected_mean=Fraction(1, 2),
    ),
    GlmVector(
        id="third-8",
        x=Fraction(1, 3),
        samples=8,
        quantum=Fraction(1),
        full_scale=Fraction(1),
        integrator_limit=Fraction(8),
        expected_code=(0, 1, 1, 0, 0, 0, 0, 1),
        expected_mean=Fraction(3, 8),
    ),
    GlmVector(
        id="two-fifths-12",
        x=Fraction(2, 5),
        samples=12,
        quantum=Fraction(1),
        full_scale=Fraction(1),
        integrator_limit=Fraction(8),
        expected_code=(0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0),
        expected_mean=Fraction(5, 12),
    ),
)

KCL_VECTORS: tuple[KclVector, ...] = (
    KclVector(
        id="half-plus-third",
        a=Fraction(1, 2),
        b=Fraction(1, 3),
        expected=Fraction(5, 6),
    ),
    KclVector(
        id="negative-plus-half",
        a=Fraction(-1, 4),
        b=Fraction(1, 2),
        expected=Fraction(1, 4),
    ),
    KclVector(
        id="zero-plus-third",
        a=Fraction(0),
        b=Fraction(1, 3),
        expected=Fraction(1, 3),
    ),
)

OPAMP_VECTORS: tuple[KclVector, ...] = (
    KclVector(
        id="opamp-half-plus-third",
        a=Fraction(1, 2),
        b=Fraction(1, 3),
        expected=Fraction(5, 6),
    ),
    KclVector(
        id="opamp-negative-plus-half",
        a=Fraction(-1, 4),
        b=Fraction(1, 2),
        expected=Fraction(1, 4),
    ),
    KclVector(
        id="opamp-zero-plus-third",
        a=Fraction(0),
        b=Fraction(1, 3),
        expected=Fraction(1, 3),
    ),
)

OPAMP_DIFFERENCE_VECTORS: tuple[KclVector, ...] = (
    KclVector(
        id="opamp-half-minus-third",
        a=Fraction(1, 2),
        b=Fraction(1, 3),
        expected=Fraction(1, 6),
    ),
    KclVector(
        id="opamp-negative-minus-half",
        a=Fraction(-1, 4),
        b=Fraction(1, 2),
        expected=Fraction(-3, 4),
    ),
    KclVector(
        id="opamp-zero-minus-third",
        a=Fraction(0),
        b=Fraction(1, 3),
        expected=Fraction(-1, 3),
    ),
)

SQRT_VECTORS: tuple[SqrtVector, ...] = (
    SqrtVector(
        id="sqrt-two",
        x=Fraction(2),
        precision=20,
        tolerance=Fraction(1, 10000),
    ),
    SqrtVector(
        id="sqrt-half",
        x=Fraction(1, 2),
        precision=20,
        tolerance=Fraction(1, 10000),
    ),
    SqrtVector(
        id="sqrt-nine",
        x=Fraction(9),
        precision=20,
        tolerance=Fraction(1, 10000),
    ),
)

EXP_VECTORS: tuple[ArithmeticVector, ...] = (
    ArithmeticVector(id="exp-zero", operation="exp", x=Fraction(0)),
    ArithmeticVector(id="exp-half", operation="exp", x=Fraction(1, 2)),
    ArithmeticVector(id="exp-negative-half", operation="exp", x=Fraction(-1, 2)),
)

LOG_VECTORS: tuple[ArithmeticVector, ...] = (
    ArithmeticVector(id="log-one", operation="log", x=Fraction(1)),
    ArithmeticVector(id="log-two", operation="log", x=Fraction(2)),
    ArithmeticVector(id="log-half", operation="log", x=Fraction(1, 2)),
)

MULT_VECTORS: tuple[ArithmeticVector, ...] = (
    ArithmeticVector(id="mult-three-quarters-two-thirds", operation="mult",
                     a=Fraction(3, 4), b=Fraction(2, 3)),
    ArithmeticVector(id="mult-half-third", operation="mult",
                     a=Fraction(1, 2), b=Fraction(1, 3)),
    ArithmeticVector(id="mult-two-half", operation="mult",
                     a=Fraction(2), b=Fraction(1, 2)),
)

DIV_VECTORS: tuple[ArithmeticVector, ...] = (
    ArithmeticVector(id="div-half-three-quarters", operation="div",
                     a=Fraction(1, 2), b=Fraction(3, 4)),
    ArithmeticVector(id="div-three-quarters-half", operation="div",
                     a=Fraction(3, 4), b=Fraction(1, 2)),
    ArithmeticVector(id="div-third-two-thirds", operation="div",
                     a=Fraction(1, 3), b=Fraction(2, 3)),
)

RECIPROCAL_VECTORS: tuple[ArithmeticVector, ...] = (
    ArithmeticVector(id="reciprocal-three-quarters", operation="reciprocal",
                     x=Fraction(3, 4)),
    ArithmeticVector(id="reciprocal-half", operation="reciprocal",
                     x=Fraction(1, 2)),
    ArithmeticVector(id="reciprocal-two", operation="reciprocal",
                     x=Fraction(2)),
)

MULT_DIV_VECTORS: tuple[ArithmeticVector, ...] = (
    ArithmeticVector(id="mult-div-half-two-half", operation="mult-div",
                     a=Fraction(1, 2), b=Fraction(2), c=Fraction(1, 2)),
    ArithmeticVector(id="mult-div-three-quarters-half-quarter", operation="mult-div",
                     a=Fraction(3, 4), b=Fraction(1, 2), c=Fraction(1, 4)),
    ArithmeticVector(id="mult-div-two-three-four", operation="mult-div",
                     a=Fraction(2), b=Fraction(3), c=Fraction(4)),
)

MULT_RECIPROCAL_VECTORS: tuple[ArithmeticVector, ...] = (
    ArithmeticVector(id="mult-reciprocal-half-two", operation="mult-reciprocal",
                     a=Fraction(1, 2), b=Fraction(2)),
    ArithmeticVector(id="mult-reciprocal-three-quarters-half", operation="mult-reciprocal",
                     a=Fraction(3, 4), b=Fraction(1, 2)),
    ArithmeticVector(id="mult-reciprocal-two-three", operation="mult-reciprocal",
                     a=Fraction(2), b=Fraction(3)),
)

DIV_MULT_VECTORS: tuple[ArithmeticVector, ...] = (
    ArithmeticVector(id="div-mult-half-two-three", operation="div-mult",
                     a=Fraction(1, 2), b=Fraction(2), c=Fraction(3)),
    ArithmeticVector(id="div-mult-three-quarters-half-third", operation="div-mult",
                     a=Fraction(3, 4), b=Fraction(1, 2), c=Fraction(1, 3)),
    ArithmeticVector(id="div-mult-two-three-four", operation="div-mult",
                     a=Fraction(2), b=Fraction(3), c=Fraction(4)),
)

FLUID_VECTORS: tuple[FluidVector, ...] = (
    FluidVector(
        id="flow-half-plus-third",
        a=Fraction(1, 2),
        b=Fraction(1, 3),
        expected=Fraction(5, 6),
    ),
    FluidVector(
        id="flow-negative-plus-half",
        a=Fraction(-1, 4),
        b=Fraction(1, 2),
        expected=Fraction(1, 4),
    ),
    FluidVector(
        id="flow-zero-plus-third",
        a=Fraction(0),
        b=Fraction(1, 3),
        expected=Fraction(1, 3),
    ),
)

FLUID_DIFFERENCE_VECTORS: tuple[FluidVector, ...] = (
    FluidVector(
        id="flow-half-minus-third",
        a=Fraction(1, 2),
        b=Fraction(1, 3),
        expected=Fraction(1, 6),
    ),
    FluidVector(
        id="flow-negative-minus-half",
        a=Fraction(-1, 4),
        b=Fraction(1, 2),
        expected=Fraction(-3, 4),
    ),
    FluidVector(
        id="flow-zero-minus-third",
        a=Fraction(0),
        b=Fraction(1, 3),
        expected=Fraction(-1, 3),
    ),
)

KCL_DIFFERENCE_VECTORS: tuple[KclVector, ...] = (
    KclVector(
        id="half-minus-third",
        a=Fraction(1, 2),
        b=Fraction(1, 3),
        expected=Fraction(1, 6),
    ),
    KclVector(
        id="negative-minus-half",
        a=Fraction(-1, 4),
        b=Fraction(1, 2),
        expected=Fraction(-3, 4),
    ),
    KclVector(
        id="zero-minus-third",
        a=Fraction(0),
        b=Fraction(1, 3),
        expected=Fraction(-1, 3),
    ),
)

SIGN_VECTORS = (
    SignVector(id="sign-negative-half", x=Fraction(-5, 2), expected=-1),
    SignVector(id="sign-zero", x=Fraction(0), expected=0),
    SignVector(id="sign-positive-third", x=Fraction(1, 3), expected=1),
)


def exact_sign_reference(x: Any) -> SignRun:
    """Exact three-level sign with no float and no undeclared state."""
    value = _fraction(x, "x")
    result = int(exact_sign(value))
    return SignRun(
        adapter="glm-reference-threshold-sign",
        x=value,
        result=result,
        passed=result in {-1, 0, 1},
    )


DELTA_SIGMA_ADAPTER = AdapterSpec(
    id="glm-reference-delta-sigma-quantized-carry",
    operation="quantized_carry",
    mechanism="delta-sigma-error-feedback",
    entrypoint="delta_sigma_quantized_carry",
    function=delta_sigma_quantized_carry,
    description=(
        "Exact first-order error-feedback quantized carry with a bounded "
        "accumulator, declared route timing and a declared code mean."
    ),
    vectors=FIXED_VECTORS,
)

KCL_ADAPTER = AdapterSpec(
    id="glm-reference-kcl-exact-sum",
    operation="sum",
    mechanism="kcl-conservation",
    entrypoint="exact_kcl_sum",
    function=exact_kcl_sum,
    description=(
        "Exact rational KCL sum with no state or feedback; the target result "
        "is compared against the declared junction route."
    ),
    vectors=KCL_VECTORS,
    kind="exact_sum",
)

FLUID_ADAPTER = AdapterSpec(
    id="glm-reference-fluid-exact-sum",
    operation="sum",
    mechanism="fluid-continuity",
    entrypoint="exact_fluid_sum",
    function=exact_fluid_sum,
    description=(
        "Exact normalized-flow fluid-continuity sum with no state or feedback; "
        "the target result is compared against the declared pipe-junction route. "
        "No pressure scaling, leakage or finite response is modeled."
    ),
    vectors=FLUID_VECTORS,
    kind="fluid_sum",
)

OPAMP_ADAPTER = AdapterSpec(
    id="glm-reference-opamp-exact-sum",
    operation="sum",
    mechanism="opamp-summing",
    entrypoint="exact_opamp_sum",
    function=exact_opamp_sum,
    description=(
        "Ideal normalized-voltage op-amp summing amplifier with a matched input "
        "network and closed-loop gain 2; the target result is compared against "
        "the declared op-amp route. No resistor mismatch, offset, finite "
        "bandwidth or device values are modeled."
    ),
    vectors=OPAMP_VECTORS,
    kind="opamp_sum",
)

OPAMP_DIFFERENCE_ADAPTER = AdapterSpec(
    id="glm-reference-opamp-exact-difference",
    operation="difference",
    mechanism="opamp-summing",
    entrypoint="exact_opamp_difference",
    function=exact_opamp_difference,
    description=(
        "Ideal normalized-voltage op-amp difference using an inverting buffer "
        "plus the matched summing amplifier; the target result is compared "
        "against the declared op-amp difference route. No resistor mismatch, "
        "offset, finite bandwidth or device values are modeled."
    ),
    vectors=OPAMP_DIFFERENCE_VECTORS,
    kind="opamp_difference",
)

FLUID_DIFFERENCE_ADAPTER = AdapterSpec(
    id="glm-reference-fluid-exact-difference",
    operation="difference",
    mechanism="fluid-continuity",
    entrypoint="exact_fluid_difference",
    function=exact_fluid_difference,
    description=(
        "Exact normalized-flow fluid-continuity difference using a declared "
        "reversed port plus the exact junction; the target result is compared "
        "against the declared pipe-junction difference route. No pressure "
        "scaling, leakage or finite response is modeled."
    ),
    vectors=FLUID_DIFFERENCE_VECTORS,
    kind="fluid_difference",
)

KCL_DIFFERENCE_ADAPTER = AdapterSpec(
    id="glm-reference-kcl-exact-difference",
    operation="difference",
    mechanism="kcl-conservation",
    entrypoint="exact_kcl_difference",
    function=exact_kcl_difference,
    description=(
        "Exact rational KCL difference using declared negation plus exact sum; "
        "the target result is compared against the source difference route."
    ),
    vectors=KCL_DIFFERENCE_VECTORS,
    kind="exact_difference",
)

SQRT_ADAPTER = AdapterSpec(
    id="glm-reference-log-domain-sqrt",
    operation="sqrt",
    mechanism="log-domain-sqrt",
    entrypoint="log_domain_sqrt",
    function=log_domain_sqrt,
    description=(
        "Target-side exact-rational log/antilog square root with a certified "
        "enclosure and an independent sqrt_q baseline; no source assembly call."
    ),
    vectors=SQRT_VECTORS,
    kind="certified_enclosure",
)

EXP_ADAPTER = AdapterSpec(
    id="glm-reference-log-domain-exp",
    operation="exp",
    mechanism="log-domain-arithmetic",
    entrypoint="log_domain_exp",
    function=log_domain_exp,
    description=(
        "Target-side certified exp(x) from the antilog junction; uses the "
        "declared interval exponential and a higher-precision reference enclosure."
    ),
    vectors=EXP_VECTORS,
    kind="certified_enclosure",
)

LOG_ADAPTER = AdapterSpec(
    id="glm-reference-log-domain-log",
    operation="log",
    mechanism="log-domain-arithmetic",
    entrypoint="log_domain_log",
    function=log_domain_log,
    description=(
        "Target-side certified log(x) from the logging junction; uses the "
        "declared interval logarithm and a higher-precision reference enclosure."
    ),
    vectors=LOG_VECTORS,
    kind="certified_enclosure",
)

MULT_ADAPTER = AdapterSpec(
    id="glm-reference-log-domain-mult",
    operation="mult",
    mechanism="log-domain-arithmetic",
    entrypoint="log_domain_mult",
    function=log_domain_mult,
    description=(
        "Target-side exp(log(a) + log(b)) multiplication with an exact "
        "rational product checker; positive normalized inputs only."
    ),
    vectors=MULT_VECTORS,
    kind="certified_enclosure",
)

DIV_ADAPTER = AdapterSpec(
    id="glm-reference-log-domain-div",
    operation="div",
    mechanism="log-domain-arithmetic",
    entrypoint="log_domain_div",
    function=log_domain_div,
    description=(
        "Target-side exp(log(a) - log(b)) division with an exact rational "
        "quotient checker; positive normalized inputs only."
    ),
    vectors=DIV_VECTORS,
    kind="certified_enclosure",
)

MULT_DIV_ADAPTER = AdapterSpec(
    id="glm-reference-log-domain-mult-div",
    operation="mult-div",
    mechanism="log-domain-arithmetic",
    entrypoint="log_domain_mult_div",
    function=log_domain_mult_div,
    description=(
        "Target-side composed exp(log(a) + log(b) - log(c)) enclosure with an "
        "exact rational (a*b)/c checker; positive normalized inputs only."
    ),
    vectors=MULT_DIV_VECTORS,
    kind="composed_certified_enclosure",
)

DIV_MULT_ADAPTER = AdapterSpec(
    id="glm-reference-log-domain-div-mult",
    operation="div-mult",
    mechanism="log-domain-arithmetic",
    entrypoint="log_domain_div_mult",
    function=log_domain_div_mult,
    description=(
        "Target-side composed exp(log(a) - log(b) + log(c)) enclosure with an "
        "exact (a*c)/b checker; positive normalized inputs only."
    ),
    vectors=DIV_MULT_VECTORS,
    kind="composed_certified_enclosure",
)

MULT_RECIPROCAL_ADAPTER = AdapterSpec(
    id="glm-reference-log-domain-mult-reciprocal",
    operation="mult-reciprocal",
    mechanism="log-domain-arithmetic",
    entrypoint="log_domain_mult_reciprocal",
    function=log_domain_mult_reciprocal,
    description=(
        "Target-side composed exp(-(log(a) + log(b))) enclosure with an exact "
        "1/(a*b) checker; positive normalized inputs only."
    ),
    vectors=MULT_RECIPROCAL_VECTORS,
    kind="composed_certified_enclosure",
)

RECIPROCAL_ADAPTER = AdapterSpec(
    id="glm-reference-log-domain-reciprocal",
    operation="reciprocal",
    mechanism="log-domain-arithmetic",
    entrypoint="log_domain_reciprocal",
    function=log_domain_reciprocal,
    description=(
        "Target-side exp(-log(x)) reciprocal with an exact rational reciprocal "
        "checker; positive normalized inputs only."
    ),
    vectors=RECIPROCAL_VECTORS,
    kind="certified_enclosure",
)

SIGN_ADAPTER = AdapterSpec(
    id="glm-reference-threshold-sign",
    operation="sign",
    mechanism="threshold-comparator",
    entrypoint="exact_sign_reference",
    function=exact_sign_reference,
    description=(
        "Exact three-level sign reference for the declared threshold "
        "comparator: negative, zero and positive branches are tested without "
        "binary float or hidden state."
    ),
    vectors=SIGN_VECTORS,
    kind="exact_sign",
)


ADAPTERS: dict[tuple[str, str], AdapterSpec] = {
    (DELTA_SIGMA_ADAPTER.operation, DELTA_SIGMA_ADAPTER.mechanism): DELTA_SIGMA_ADAPTER,
    (KCL_ADAPTER.operation, KCL_ADAPTER.mechanism): KCL_ADAPTER,
    (OPAMP_ADAPTER.operation, OPAMP_ADAPTER.mechanism): OPAMP_ADAPTER,
    (OPAMP_DIFFERENCE_ADAPTER.operation, OPAMP_DIFFERENCE_ADAPTER.mechanism): OPAMP_DIFFERENCE_ADAPTER,
    (FLUID_ADAPTER.operation, FLUID_ADAPTER.mechanism): FLUID_ADAPTER,
    (FLUID_DIFFERENCE_ADAPTER.operation, FLUID_DIFFERENCE_ADAPTER.mechanism): FLUID_DIFFERENCE_ADAPTER,
    (KCL_DIFFERENCE_ADAPTER.operation, KCL_DIFFERENCE_ADAPTER.mechanism): KCL_DIFFERENCE_ADAPTER,
    (SQRT_ADAPTER.operation, SQRT_ADAPTER.mechanism): SQRT_ADAPTER,
    (EXP_ADAPTER.operation, EXP_ADAPTER.mechanism): EXP_ADAPTER,
    (LOG_ADAPTER.operation, LOG_ADAPTER.mechanism): LOG_ADAPTER,
    (MULT_ADAPTER.operation, MULT_ADAPTER.mechanism): MULT_ADAPTER,
    (DIV_ADAPTER.operation, DIV_ADAPTER.mechanism): DIV_ADAPTER,
    (RECIPROCAL_ADAPTER.operation, RECIPROCAL_ADAPTER.mechanism): RECIPROCAL_ADAPTER,
    (SIGN_ADAPTER.operation, SIGN_ADAPTER.mechanism): SIGN_ADAPTER,
}


def get_adapter(operation: str, mechanism: str | None = None) -> AdapterSpec:
    """Return the declared executable adapter, or fail explicitly."""
    matches = [
        spec
        for (candidate_operation, candidate_mechanism), spec in ADAPTERS.items()
        if candidate_operation == operation
        and (mechanism is None or candidate_mechanism == mechanism)
    ]
    if not matches:
        detail = f"{operation!r}"
        if mechanism is not None:
            detail += f" via {mechanism!r}"
        known = ", ".join(f"{op}/{mech}" for op, mech in sorted(ADAPTERS))
        raise KeyError(f"no target adapter for {detail}; declared: {known}")
    if len(matches) > 1:
        raise ValueError(
            f"ambiguous target adapter for {operation!r}; declare a mechanism"
        )
    return matches[0]


GLM_REFERENCE_TARGET = TargetProfile(
    id=TARGET_ID,
    kind="software",
    description=(
        "Declared exact-rational software target for quantized-carry, exact KCL and "
        "normalized fluid sum, exact-difference, log-domain square-root, "
        "arithmetic operations including positive reciprocal, and three-level "
        "sign. It is a "
        "reference adapter experiment, not a GLM model, a GLM runtime or a "
        "performance measurement."
    ),
    interface={
        "contract": "python callable with exact rational inputs and JSON-safe outputs",
        "operations": ["quantized_carry", "sum", "difference", "sqrt", "exp", "log", "mult", "div", "reciprocal", "sign"],
        "interfaces": {
            "quantized_carry": {
                "inputs": {
                    "x": "exact rational in [0, full_scale]",
                    "samples": "positive integer",
                    "quantum": "positive exact rational",
                    "full_scale": "positive integer multiple of quantum",
                    "integrator_limit": "positive exact rational",
                },
                "outputs": {
                    "code": "bounded integer code sequence",
                    "mean": "exact rational code mean",
                    "error": "mean - x",
                    "peak_state": "nonnegative exact rational",
                    "bounded": "boolean",
                    "passed": "boolean for bounded state and declared reconstruction",
                },
                "state": "one exact rational accumulator plus the declared feedback history",
                "feedback": "delayed quantized level matching the exact route's effective loop history",
            },
            "sum": {
                "inputs": {"a": "exact rational", "b": "exact rational"},
                "outputs": {"total": "exact rational"},
                "state": "none",
                "feedback": "none",
            },
            "difference": {
                "inputs": {"a": "exact rational", "b": "exact rational"},
                "outputs": {"total": "exact rational"},
                "state": "none",
                "feedback": "none",
                "law": "a - b is negation of b followed by exact sum",
            },
            "sqrt": {
                "inputs": {
                    "x": "positive exact rational",
                    "precision": "integer in 1..64",
                    "tolerance": "positive exact rational",
                },
                "outputs": {
                    "root": "certified rational enclosure",
                    "checker": "independent sqrt_q enclosure",
                    "passed": "boolean for overlap and declared width",
                },
                "state": "none",
                "feedback": "none",
                "law": "root = exp((1/2) * log(x))",
            },
            "exp": {
                "inputs": {"x": "exact rational", "precision": "integer in 1..64",
                           "tolerance": "positive exact rational"},
                "outputs": {"value": "certified rational enclosure of exp(x)",
                            "checker": "higher-precision exp_q enclosure",
                            "passed": "boolean for overlap and declared width"},
                "state": "none", "feedback": "none",
                "law": "value = exp(x)",
            },
            "log": {
                "inputs": {"x": "positive exact rational", "precision": "integer in 1..64",
                           "tolerance": "positive exact rational"},
                "outputs": {"value": "certified rational enclosure of log(x)",
                            "checker": "higher-precision log_q enclosure",
                            "passed": "boolean for overlap and declared width"},
                "state": "none", "feedback": "none",
                "law": "value = log(x)",
            },
            "mult": {
                "inputs": {"a": "positive exact rational", "b": "positive exact rational",
                           "precision": "integer in 1..64", "tolerance": "positive exact rational"},
                "outputs": {"value": "certified rational enclosure of a*b",
                            "checker": "exact rational product",
                            "passed": "boolean for containment and declared width"},
                "state": "none", "feedback": "none",
                "law": "value = exp(log(a) + log(b))",
            },
            "div": {
                "inputs": {"a": "positive exact rational", "b": "positive exact rational",
                           "precision": "integer in 1..64", "tolerance": "positive exact rational"},
                "outputs": {"value": "certified rational enclosure of a/b",
                            "checker": "exact rational quotient",
                            "passed": "boolean for containment and declared width"},
                "state": "none", "feedback": "none",
                "law": "value = exp(log(a) - log(b))",
            },
            "reciprocal": {
                "inputs": {"x": "positive exact rational",
                           "precision": "integer in 1..64", "tolerance": "positive exact rational"},
                "outputs": {"value": "certified rational enclosure of 1/x",
                            "checker": "exact rational reciprocal",
                            "passed": "boolean for containment and declared width"},
                "state": "none", "feedback": "none",
                "law": "value = exp(-log(x))",
            },
            "sign": {
                "inputs": {"x": "exact rational"},
                "outputs": {"value": "integer in {-1, 0, 1}"},
                "state": "none", "feedback": "none",
                "law": "value = -1 if x < 0; 0 if x = 0; +1 if x > 0",
            },
        },
        "precision": "exact rational",
        "latency": {
            "kind": "declared reference-operation step count",
            "unit": "steps",
            "quantized_carry": "samples",
            "sum": 1,
            "difference": 1,
            "sqrt": "1 route evaluation",
            "exp": "1 route evaluation",
            "log": "1 route evaluation",
            "mult": "2 log stages + 1 sum + 1 antilog",
            "div": "2 log stages + 1 negation + 1 sum + 1 antilog",
            "reciprocal": "1 log stage + 1 negation + 1 antilog",
            "sign": 1,
        },
        "bit_budget": {
            "kind": "declared reference-operation output width",
            "unit": "bits",
            "quantized_carry": "ceil(log2(full_scale / quantum + 1)) per code",
            "sum": "exact rational result; no fixed-width limit",
            "difference": "exact rational result; no fixed-width limit",
            "sqrt": "precision bits per enclosure",
            "exp": "precision bits per enclosure",
            "log": "precision bits per enclosure",
            "mult": "precision bits per enclosure",
            "div": "precision bits per enclosure",
            "reciprocal": "precision bits per enclosure",
            "sign": "2 bits for the three-level output {-1, 0, +1}",
        },
    },
    constraints={
        "exact_rational": True,
        "no_binary_float": True,
        "reference_only": True,
        "no_real_glm_interface": True,
        "no_glm_performance_claim": True,
        "reference_budgets_declared": True,
        "fixed_test_vectors": True,
    },
    evidence_required=("executable target adapter", "fixed target vectors", "pass/fail certificate"),
    provenance=(
        "docs/TRANSFER_COMPILER_OBJECTIVE.md",
        "cent_compiler/assembly.py",
        "cent_compiler/targets/glm.py",
    ),
    gaps=(
        "no real GLM interface, model call or runtime integration",
        "reference-operation latency and bit budgets are declared; no external GLM, numerical-backend or hardware budget is connected",
        "no GLM performance improvement or measured target result is claimed",
    ),
)
GLM_REFERENCE_TARGET.validate()


__all__ = [
    "ADAPTERS",
    "ADAPTER_SCHEMA",
    "AdapterSpec",
    "DELTA_SIGMA_ADAPTER",
    "DIV_ADAPTER",
    "DIV_VECTORS",
    "EXP_ADAPTER",
    "EXP_VECTORS",
    "LOG_ADAPTER",
    "LOG_VECTORS",
    "MULT_ADAPTER",
    "DIV_MULT_ADAPTER",
    "DIV_MULT_VECTORS",
    "MULT_DIV_ADAPTER",
    "MULT_DIV_VECTORS",
    "MULT_RECIPROCAL_ADAPTER",
    "MULT_RECIPROCAL_VECTORS",
    "MULT_VECTORS",
    "log_domain_div_mult",
    "log_domain_mult_div",
    "log_domain_mult_reciprocal",
    "RECIPROCAL_ADAPTER",
    "RECIPROCAL_VECTORS",
    "SIGN_ADAPTER",
    "SIGN_VECTORS",
    "SignRun",
    "SignVector",
    "exact_sign_reference",
    "ArithmeticTargetRun",
    "ArithmeticVector",
    "FIXED_VECTORS",
    "FLUID_ADAPTER",
    "FLUID_DIFFERENCE_ADAPTER",
    "OPAMP_ADAPTER",
    "OPAMP_DIFFERENCE_ADAPTER",
    "OPAMP_DIFFERENCE_VECTORS",
    "OPAMP_VECTORS",
    "FLUID_DIFFERENCE_VECTORS",
    "FLUID_VECTORS",
    "FluidVector",
    "GLM_REFERENCE_TARGET",
    "GlmVector",
    "KCL_ADAPTER",
    "KCL_DIFFERENCE_ADAPTER",
    "KCL_DIFFERENCE_VECTORS",
    "KCL_VECTORS",
    "KclVector",
    "SQRT_ADAPTER",
    "SQRT_VECTORS",
    "SqrtTargetRun",
    "SqrtVector",
    "SumRun",
    "TARGET_ID",
    "TargetRun",
    "delta_sigma_quantized_carry",
    "exact_fluid_difference",
    "exact_fluid_sum",
    "exact_opamp_difference",
    "exact_opamp_sum",
    "exact_kcl_difference",
    "exact_kcl_sum",
    "get_adapter",
    "log_domain_reciprocal",
    "log_domain_sqrt",
    "uniform_quantizer_carry",
]
