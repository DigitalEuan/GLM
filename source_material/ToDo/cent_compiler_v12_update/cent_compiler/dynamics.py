"""Exact sampled-data checks for declared physical routes.

The static design and netlist layers answer "what values and topology?".
This layer asks "what happens over time?" for routes whose declared quantities
actually contain a time constant.

The first model is the delta-sigma RC integrator.  Input and feedback are held
constant over one clock, the comparator samples the integrator state at the
start of the tick, and the state advances by the exact first-order step:

    V[n+1] = V[n] + (1 - exp(-T/tau)) * (V_in - V_fb[n])

The exponential is a certified rational enclosure, not a binary float.  This
immediately exposes a real limitation: the static binding's unit increment is
the asymptotic gain, while the declared ``tau = T_clock`` gives only
``1 - exp(-1)`` per tick.  The dynamic report keeps that mismatch explicit.

The log-domain and feedback routes declare reference capacitance and timing
quantities, so they run nonlinear large-signal backward-Euler transients: a
two-node diode/load ODE and a quadratic multiplier feedback loop.  These are
declared reference models, not measured device models.  They use adaptive
step doubling with an exact local budget, plus a continuous forward-invariance
bounded-state certificate that can fail on a caller-supplied too-small box.
A conditional Gronwall envelope is attempted, but its local term is still a
step-doubling estimate, so a formal global ODE error bound remains an
explicit gap.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Callable, Mapping

from .design import DesignResult, solve_route
from .device import DeviceBinding
from .exact import CentError, ErrorCode, Q, q as exact_q, q_to_json
from .interval import Interval, as_interval, exp_q, log_q, sqrt_q

SCHEMA = "cent-dynamics/1"
DEFAULT_SAMPLES = 64
MAX_SAMPLES = 256
DYNAMIC_PRECISION = 80
CERTIFICATE_BOX_KEYS = {
    "sqrt-log": ("v_log_hi", "v_out_hi"),
    "sqrt-feedback": ("v_hi",),
}
"""Required caller-supplied certificate-box keys for each compute route."""


def _json(value: Any) -> Any:
    """Encode exact rationals and enclosures for the public payload."""
    if isinstance(value, Fraction):
        return q_to_json(value)
    if isinstance(value, Interval):
        return {
            "lo": q_to_json(value.lo),
            "hi": q_to_json(value.hi),
            "width": q_to_json(value.width),
        }
    if isinstance(value, Mapping):
        return {str(key): _json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json(item) for item in value]
    return value


def _decimal(value: Q, places: int = 18) -> str:
    """Deterministic decimal truncation using integer arithmetic only."""
    sign = "-" if value < 0 else ""
    value = abs(value)
    scale = 10 ** places
    scaled = value.numerator * scale // value.denominator
    return f"{sign}{scaled // scale}.{scaled % scale:0{places}d}"


def _round_up(value: Q, places: int = 18) -> Q:
    """Round a certified upper bound outward on a bounded decimal grid."""
    scale = 10 ** places
    scaled = value * scale
    upper = -((-scaled.numerator) // scaled.denominator)
    return Fraction(upper, scale)


def _round_down(value: Q, places: int = 18) -> Q:
    """Round a certified lower bound outward on a bounded decimal grid."""
    scale = 10 ** places
    scaled = value * scale
    lower = scaled.numerator // scaled.denominator
    return Fraction(lower, scale)


def _display_certificate(certificate: Mapping[str, Any]) -> dict[str, Any]:
    """Round certificate display data without changing the proof inputs."""
    display = dict(certificate)
    if "box" in certificate:
        display["box"] = {
            key: (
                _round_down(value, 12)
                if key.endswith("_lo")
                else _round_up(value, 12)
            )
            for key, value in certificate["box"].items()
        }
    if "boundary" in certificate:
        display["boundary"] = {
            key: _round_outward(value, 12)
            for key, value in certificate["boundary"].items()
        }
    return display


def _validate_samples(samples: Any) -> int:
    if isinstance(samples, bool):
        raise CentError(ErrorCode.TYPE_ERROR, "samples must be an integer")
    try:
        count = int(samples)
    except (TypeError, ValueError) as exc:
        raise CentError(ErrorCode.TYPE_ERROR, "samples must be an integer") from exc
    if not 1 <= count <= MAX_SAMPLES:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            f"samples must be in 1..{MAX_SAMPLES}",
        )
    return count


def _certificate_box_value(value: Any, key: str) -> Q:
    """Parse one exact certificate-box bound, rejecting binary floats."""
    name = f"certificate_box.{key}"
    if isinstance(value, bool):
        raise CentError(ErrorCode.TYPE_ERROR, f"{name}: bool is not a quantity")
    if isinstance(value, str) and "/" in value:
        try:
            parsed = Fraction(value.strip())
        except (ValueError, ZeroDivisionError) as exc:
            raise CentError(
                ErrorCode.INVALID_INPUT,
                f"{name}: not an exact fraction: {value!r}",
            ) from exc
    else:
        parsed = exact_q(value, name)
    if parsed <= 0:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            f"{name}: certificate-box bounds must be positive",
        )
    return parsed


def _validate_certificate_box(
    route_key: str,
    box: Mapping[str, Any] | None,
) -> dict[str, Q] | None:
    """Validate a caller-supplied state box without widening it."""
    if box is None:
        return None
    keys = CERTIFICATE_BOX_KEYS.get(route_key)
    if keys is None:
        raise CentError(
            ErrorCode.INVALID_INPUT,
            f"certificate box is not defined for route {route_key!r}",
        )
    if not isinstance(box, Mapping):
        raise CentError(
            ErrorCode.TYPE_ERROR,
            "certificate_box must be an object of exact bounds",
        )
    unexpected = sorted(set(box) - set(keys), key=str)
    if unexpected:
        raise CentError(
            ErrorCode.INVALID_INPUT,
            "certificate_box has unexpected key(s): "
            + ", ".join(str(key) for key in unexpected),
        )
    missing = [key for key in keys if key not in box]
    if missing:
        raise CentError(
            ErrorCode.INVALID_INPUT,
            "certificate_box needs " + ", ".join(keys),
        )
    return {
        key: _certificate_box_value(box[key], key)
        for key in keys
    }


def _quantity(binding: DeviceBinding, symbol: str) -> Any:
    for item in binding.quantities:
        if item.symbol == symbol:
            return item.value
    raise CentError(
        ErrorCode.VALIDATION_ERROR,
        f"dynamic model needs the declared quantity {symbol!r}",
    )


def _round_outward(value: Interval, places: int = 12) -> Interval:
    """Widen an enclosure to a bounded decimal rational grid."""
    scale = 10 ** places
    lo_scaled = value.lo * scale
    hi_scaled = value.hi * scale
    lo = lo_scaled.numerator // lo_scaled.denominator
    hi = -((-hi_scaled.numerator) // hi_scaled.denominator)
    return Interval(Fraction(lo, scale), Fraction(hi, scale))


NONLINEAR_PRECISION = 32
NONLINEAR_BISECTION = 36
NONLINEAR_ROUND = 12
NONLINEAR_GRID = 9

ADAPTIVE_ATOL_LOG = Fraction(1, 10**5)
ADAPTIVE_ATOL_OUT = Fraction(1, 10**4)
ADAPTIVE_RTOL = Fraction(1, 10**6)
ADAPTIVE_MAX_STEPS = 20_000
ADAPTIVE_MIN_STEP = Fraction(1, 10**24)
ADAPTIVE_STEP_PLACES = 21

CERTIFICATE_ERROR_TARGET = Fraction(1, 1000)
CERTIFICATE_GRONWALL_LIMIT = Fraction(50)


def _midpoint(value: Any) -> Q:
    return value.midpoint if isinstance(value, Interval) else value


def _bracket_increasing(
    func,
    center: Q,
    width: Q,
    *,
    max_expand: int = 80,
) -> tuple[Q, Q]:
    """Find a bracket around a monotone increasing root."""
    lo = center - width
    hi = center + width
    flo = func(lo)
    fhi = func(hi)
    for _ in range(max_expand):
        if _midpoint(flo) <= 0:
            break
        lo -= width
        flo = func(lo)
    else:
        raise CentError(ErrorCode.DOMAIN_ERROR, "could not bracket dynamic root below")
    for _ in range(max_expand):
        if _midpoint(fhi) >= 0:
            break
        hi += width
        fhi = func(hi)
    else:
        raise CentError(ErrorCode.DOMAIN_ERROR, "could not bracket dynamic root above")
    return lo, hi


def _bisect_increasing(
    func,
    lo: Q,
    hi: Q,
    *,
    steps: int = NONLINEAR_BISECTION,
    places: int | None = None,
) -> Interval:
    """Bisect a monotone increasing function and return an interval root.

    With ``places``, the search runs on a fixed decimal grid.  That keeps every
    exponential argument's denominator bounded instead of growing a fresh
    power of two on each halving.
    """
    if places is None:
        for _ in range(steps):
            mid = (lo + hi) / 2
            if _midpoint(func(mid)) < 0:
                lo = mid
            else:
                hi = mid
        return Interval(lo, hi)

    scale = 10 ** places
    lo_scaled = lo * scale
    hi_scaled = hi * scale
    lo_index = lo_scaled.numerator // lo_scaled.denominator
    hi_index = -((-hi_scaled.numerator) // hi_scaled.denominator)
    if lo_index > hi_index:
        raise CentError(ErrorCode.DOMAIN_ERROR, "dynamic bracket is inverted")
    for _ in range(steps):
        if hi_index - lo_index <= 1:
            break
        mid_index = (lo_index + hi_index) // 2
        mid = Fraction(mid_index, scale)
        if _midpoint(func(mid)) < 0:
            lo_index = mid_index
        else:
            hi_index = mid_index
    return Interval(Fraction(lo_index, scale), Fraction(hi_index, scale))


def _round_step(value: Q) -> Q:
    """Round a step size to a bounded decimal grid.

    Adaptive factors such as 21/20 otherwise grow an exact denominator on
    every accepted or rejected trial.  The grid is far below the smallest step
    the controller accepts, and keeps the repeated Fraction arithmetic and the
    public JSON practical.
    """
    scale = 10 ** ADAPTIVE_STEP_PLACES
    return Fraction(round(value * scale), scale)


def _scaled_step_error(
    fine: Interval,
    coarse: Interval,
    atol: Q,
    rtol: Q,
) -> Q:
    """Normalize one component's coarse/fine difference by its local budget."""
    scale = atol + rtol * max(fine.abs().hi, coarse.abs().hi)
    return (fine - coarse).abs().hi / scale


def _adaptive_integrate(
    step: Callable[[tuple[Interval, ...], Q], tuple[Interval, ...]],
    initial_state: tuple[Interval, ...],
    *,
    t_final: Q,
    samples: int,
    error: Callable[[tuple[Interval, ...], tuple[Interval, ...]], Q],
    h0: Q,
    h_max: Q,
    local_truncation: Callable[[tuple[Interval, ...], Q], tuple[Q, ...]] | None = None,
) -> tuple[list[tuple[Q, tuple[Interval, ...]]], dict[str, Any]]:
    """Integrate with exact step-doubling and a declared local error budget.

    Each trial computes one backward-Euler step of size ``h`` and two steps of
    size ``h/2``.  The enclosed coarse/fine difference is compared component by
    component with ``atol + rtol*|state|``; only trials inside that budget are
    accepted.  This controls a local step-doubling estimate, not a formal
    global ODE error bound.
    """
    sample_times = [
        t_final * index / samples for index in range(1, samples + 1)
    ]
    state = initial_state
    time = Fraction(0)
    step_size = _round_step(h0 if h0 < h_max else h_max)
    if step_size <= 0 or h_max <= 0:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            "adaptive dynamic step size must be positive",
        )
    accepted = 0
    rejected = 0
    max_ratio = Fraction(0)
    max_rejected_ratio = Fraction(0)
    local_defect_sum = Fraction(0)
    max_local_defect = Fraction(0)
    local_truncation_sums = [Fraction(0) for _ in initial_state]
    max_state_widths = [Fraction(0) for _ in initial_state]
    min_step: Q | None = None
    max_step: Q | None = None
    trace: list[tuple[Q, tuple[Interval, ...]]] = []

    for target in sample_times:
        while time < target:
            remaining = target - time
            if step_size > remaining:
                step_size = _round_step(remaining)

            coarse = step(state, step_size)
            half = step(state, step_size / 2)
            fine = step(half, step_size / 2)
            ratio = error(fine, coarse)

            if ratio <= 1:
                defect = max(
                    (fine[index] - coarse[index]).abs().hi
                    for index in range(len(fine))
                )
                local_defect_sum += defect
                if defect > max_local_defect:
                    max_local_defect = defect
                if local_truncation is not None:
                    bounds = local_truncation(state, step_size)
                    if len(bounds) != len(initial_state):
                        raise CentError(
                            ErrorCode.VALIDATION_ERROR,
                            "local truncation callback returned the wrong dimension",
                        )
                    for index, bound in enumerate(bounds):
                        if bound < 0:
                            raise CentError(
                                ErrorCode.VALIDATION_ERROR,
                                "local truncation bound must be nonnegative",
                            )
                        local_truncation_sums[index] += bound
                state = fine
                for index, item in enumerate(state):
                    if item.width > max_state_widths[index]:
                        max_state_widths[index] = item.width
                time += step_size
                accepted += 1
                if ratio > max_ratio:
                    max_ratio = ratio
                if min_step is None or step_size < min_step:
                    min_step = step_size
                if max_step is None or step_size > max_step:
                    max_step = step_size
                if ratio <= Fraction(1, 16):
                    factor = Fraction(2)
                elif ratio <= Fraction(1, 4):
                    factor = Fraction(3, 2)
                elif ratio <= Fraction(1, 2):
                    factor = Fraction(6, 5)
                elif ratio <= Fraction(4, 5):
                    factor = Fraction(21, 20)
                else:
                    factor = Fraction(1)
                step_size = _round_step(step_size * factor)
                if step_size > h_max:
                    step_size = h_max
            else:
                rejected += 1
                if ratio > max_rejected_ratio:
                    max_rejected_ratio = ratio
                factor = Fraction(4, 5) / ratio
                if factor < Fraction(1, 10):
                    factor = Fraction(1, 10)
                elif factor > Fraction(1, 2):
                    factor = Fraction(1, 2)
                step_size = _round_step(step_size * factor)
                if step_size < ADAPTIVE_MIN_STEP:
                    raise CentError(
                        ErrorCode.BUDGET_EXHAUSTED,
                        "adaptive dynamic step fell below the declared floor",
                    )

            if accepted + rejected > ADAPTIVE_MAX_STEPS:
                raise CentError(
                    ErrorCode.BUDGET_EXHAUSTED,
                    "adaptive dynamic step budget exhausted",
                )
        trace.append((target, state))

    return trace, {
        "accepted_steps": Fraction(accepted),
        "rejected_steps": Fraction(rejected),
        "min_step": min_step if min_step is not None else Fraction(0),
        "max_step": max_step if max_step is not None else Fraction(0),
        "max_local_error_ratio": max_ratio,
        "max_rejected_error_ratio": max_rejected_ratio,
        "local_defect_sum": local_defect_sum,
        "max_local_defect": max_local_defect,
        "local_truncation_sums": tuple(local_truncation_sums),
        "max_state_widths": tuple(max_state_widths),
    }


@dataclass(frozen=True)
class DynamicCheck:
    """One time-domain check, including its exact value where meaningful."""

    name: str
    status: str
    detail: str
    value: Any | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
            "value": _json(self.value) if self.value is not None else None,
        }


@dataclass(frozen=True)
class DynamicTracePoint:
    """One sampled clock tick of the dynamic model."""

    tick: int
    input_value: Q
    state_before: Interval | None = None
    state_after: Interval | None = None
    level: int | None = None
    feedback: Q | None = None
    uncertain: bool = False
    time: Q | None = None
    output: Interval | None = None
    target: Interval | None = None
    aux: Interval | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "tick": self.tick,
            "input": q_to_json(self.input_value),
        }
        if self.time is not None:
            payload["time"] = q_to_json(self.time)
        if self.state_before is not None:
            payload["state_before"] = _json(self.state_before)
        if self.state_after is not None:
            payload["state_after"] = _json(self.state_after)
        if self.level is not None:
            payload["level"] = self.level
        if self.feedback is not None:
            payload["feedback"] = q_to_json(self.feedback)
        if self.output is not None:
            payload["output"] = _json(self.output)
        if self.target is not None:
            payload["target"] = _json(self.target)
        if self.aux is not None:
            payload["aux"] = _json(self.aux)
        if self.uncertain:
            payload["uncertain"] = True
        return payload


@dataclass(frozen=True)
class DynamicResult:
    """A route's dynamic model, checks, trace, certificates and remaining gaps."""

    route_key: str
    route_id: str
    route_name: str
    model: str
    samples: int
    input_value: Q
    selected_option: str
    status: str
    metrics: Mapping[str, Any]
    checks: tuple[DynamicCheck, ...]
    trace: tuple[DynamicTracePoint, ...]
    gaps: tuple[str, ...]
    certificates: Mapping[str, Any] | None = None
    nonlinear_transient: Mapping[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "route": self.route_id,
            "route_key": self.route_key,
            "route_name": self.route_name,
            "model": self.model,
            "status": self.status,
            "samples": self.samples,
            "input": q_to_json(self.input_value),
            "selected_option": self.selected_option,
            "metrics": _json(dict(self.metrics)),
            "checks": [check.as_dict() for check in self.checks],
            "trace": [point.as_dict() for point in self.trace],
            "gaps": list(self.gaps),
            "certificates": (
                _json(dict(self.certificates)) if self.certificates else {}
            ),
            "nonlinear_transient": (
                _json(dict(self.nonlinear_transient))
                if self.nonlinear_transient
                else None
            ),
        }

    def render_text(self) -> str:
        lines = [
            "=" * 78,
            "DYNAMIC CHECK",
            "=" * 78,
            f"Route: {self.route_name} ({self.route_key})",
            f"Status: {self.status}",
            f"Model: {self.model}",
            f"Selected: {self.selected_option}",
            f"Samples: {self.samples}",
            "",
            "Metrics",
        ]
        for name, value in self.metrics.items():
            if isinstance(value, Interval):
                shown = f"[{_decimal(value.lo)}, {_decimal(value.hi)}]"
            elif isinstance(value, Fraction):
                shown = (
                    f"{value} ({_decimal(value)})"
                    if value.denominator.bit_length() <= 64
                    else _decimal(value)
                )
            else:
                shown = str(value)
            lines.append(f"  {name:<22} {shown}")
        lines.extend(("", "Checks"))
        for check in self.checks:
            lines.append(f"  [{check.status:<6}] {check.name}: {check.detail}")
        if self.nonlinear_transient:
            transient = self.nonlinear_transient
            lines.extend(
                (
                    "",
                    "Nonlinear transient",
                    f"  [{transient.get('status', 'gap')}] {transient.get('model', '')}",
                    f"  samples: {transient.get('samples', 0)}; "
                    f"substeps: {transient.get('substeps', 0)}",
                )
            )
        if self.trace:
            lines.extend(("", "Trace"))
            for point in self.trace[:12]:
                if point.state_before is not None and point.level is not None:
                    lines.append(
                        f"  t={point.tick:<3} state={_decimal(point.state_before.midpoint, 9):<12} "
                        f"level={point.level} feedback={_decimal(point.feedback or 0, 9)}"
                    )
                elif point.output is not None and point.target is not None:
                    lines.append(
                        f"  t={_decimal(point.time or 0, 12):<16} "
                        f"output={_decimal(point.output.midpoint, 12):<16} "
                        f"target={_decimal(point.target.midpoint, 12)}"
                    )
            if len(self.trace) > 12:
                lines.append(
                    f"  ... {len(self.trace) - 12} more tick(s); full exact trace in JSON"
                )
        if self.certificates:
            lines.extend(("", "Certificates"))
            for name, certificate in self.certificates.items():
                lines.append(
                    f"  [{certificate.get('status', 'gap')}] {name}: "
                    f"{certificate.get('detail', '')}"
                )
        lines.extend(("", "Remaining gaps"))
        for gap in self.gaps:
            lines.append(f"  - {gap}")
        return "\n".join(lines)


def _delta_sigma_dynamic(
    binding: DeviceBinding,
    *,
    samples: int,
    selected_option: str,
) -> DynamicResult:
    """Run the declared RC/clock loop as an exact sampled-data model."""
    q = {item.symbol: item.value for item in binding.quantities}
    input_value = binding.input_value
    v_ref = q["V_ref"]
    v_in = v_ref * input_value
    tau = q["tau"]
    clock = q["T_clock"]
    v_threshold = q["V_threshold"]
    v_offset = q["V_offset"]
    v_limit = q["V_int_limit"]
    v_lsb = q["V_lsb"]

    alpha = 1 - exp_q(-clock / tau, DYNAMIC_PRECISION)
    threshold = v_threshold + v_offset
    state = Interval.point(Fraction(0))
    peak = Fraction(0)
    levels: list[int] = []
    trace: list[DynamicTracePoint] = []
    uncertain_count = 0

    for tick in range(1, samples + 1):
        before = state
        if before.lo >= threshold:
            level = 1
            uncertain = False
        elif before.hi <= threshold:
            level = 0
            uncertain = False
        else:
            level = 1 if before.midpoint >= threshold else 0
            uncertain = True
            uncertain_count += 1
        feedback = v_ref * level
        after = before + alpha * (v_in - feedback)
        peak = max(peak, before.abs().hi, after.abs().hi)
        levels.append(level)
        trace.append(
            DynamicTracePoint(
                tick=tick,
                input_value=input_value,
                state_before=before,
                state_after=after,
                level=level,
                feedback=feedback,
                uncertain=uncertain,
            )
        )
        state = after

    mean = Fraction(sum(levels), samples)
    mean_error = mean - input_value
    quantum = v_lsb / v_ref
    tracking_ok = abs(mean_error) <= quantum
    range_ok = peak <= v_limit
    comparator_ok = uncertain_count == 0
    static_gain = Fraction(1)
    gain_deficit = static_gain - alpha

    checks = (
        DynamicCheck(
            "RC time constant",
            "pass",
            f"tau * f_clock = {q['RC_f']}; the declared clock and RC define the sampled model",
            q["RC_f"],
        ),
        DynamicCheck(
            "one-tick settling gain",
            "gap",
            "static model uses a full increment; the RC step gain is "
            f"[{_decimal(alpha.lo)}, {_decimal(alpha.hi)}], leaving a "
            f"{_decimal(gain_deficit.lo)} deficit",
            alpha,
        ),
        DynamicCheck(
            "sampled loop tracking",
            "pass" if tracking_ok else "gap",
            f"mean {mean} ({_decimal(mean)}) vs input {input_value}; "
            f"error {mean_error} <= one LSB {quantum}",
            mean,
        ),
        DynamicCheck(
            "integrator range",
            "pass" if range_ok else "gap",
            f"peak {_decimal(peak)} V <= declared limit {v_limit} V",
            peak,
        ),
        DynamicCheck(
            "comparator resolution",
            "pass" if comparator_ok else "gap",
            f"{uncertain_count} uncertain decision(s); the model uses an ideal "
            "sampled comparator",
            Fraction(uncertain_count),
        ),
    )

    if not tracking_ok or not range_ok or not comparator_ok:
        status = "gap"
    elif alpha.lo < static_gain or alpha.hi < static_gain:
        status = "partial"
    else:
        status = "pass"

    nonlinear = _delta_sigma_clocked_transient(binding, samples=samples)
    if nonlinear["status"] != "pass":
        status = "gap"
    checks = checks + (
        DynamicCheck(
            "continuous-time nonlinear transient",
            nonlinear["status"],
            f"{nonlinear['model']}; {len(nonlinear['trace'])} exact substep(s), "
            f"peak {_decimal(nonlinear['metrics']['peak_volts'])} V against "
            f"limit {_decimal(v_limit)} V",
            Fraction(len(nonlinear["trace"])),
        ),
    )

    gaps = (
        "The static binding treats one clock as a full normalized increment. "
        f"The dynamic RC step gain is only {_decimal(alpha.lo)} to "
        f"{_decimal(alpha.hi)} per clock because tau = T_clock; that finite "
        "settling is not included in the static error budget.",
        "The sampled model holds input and feedback constant for each clock, "
        "uses an ideal comparator, and does not model switch resistance, "
        "capacitor leakage, op-amp slew, clock jitter or metastability.",
        "No measured R/C values, tolerance distribution, temperature drift or "
        "transistor-level transient simulation is attached.",
    )
    if nonlinear["status"] != "pass":
        gaps = gaps + (
            f"Continuous-time nonlinear transient: {nonlinear['gaps'][0]}",
        )

    return DynamicResult(
        route_key="delta-sigma",
        route_id=binding.route_id,
        route_name="First-order delta-sigma carry route",
        model="exact sampled first-order RC integrator with clocked comparator/feedback",
        samples=samples,
        input_value=input_value,
        selected_option=selected_option,
        status=status,
        metrics={
            "time_constant": tau,
            "clock_period": clock,
            "rc_clock_ratio": q["RC_f"],
            "settling_fraction": alpha,
            "settling_deficit": gain_deficit,
            "mean": mean,
            "mean_error": mean_error,
            "peak_volts": peak,
            "quantum": quantum,
            "nonlinear_status": nonlinear["status"],
            "nonlinear_substeps": nonlinear["substeps"],
        },
        checks=checks,
        trace=tuple(trace),
        gaps=gaps,
        nonlinear_transient=nonlinear,
    )


DELTA_SIGMA_SUBSTEPS = 4


def _delta_sigma_clocked_transient(
    binding: DeviceBinding, *, samples: int
) -> dict[str, Any]:
    """Run the declared clocked-comparator/RC route as a continuous transient.

    The feedback level is decided at each clock edge and held for that clock;
    between edges the RC update is the exact first-order exponential step.  The
    clocked comparator is the nonlinear element.  State endpoints are rounded
    outward to a 12-place decimal grid after each substep so a long exact trace
    stays serializable; containment is preserved.  This is deliberately not a
    claim of a smooth nonlinear ODE or of switch-level device behavior.
    """
    q = {item.symbol: item.value for item in binding.quantities}
    input_value = binding.input_value
    v_ref = q["V_ref"]
    v_in = v_ref * input_value
    tau = q["tau"]
    clock = q["T_clock"]
    v_threshold = q["V_threshold"]
    v_offset = q["V_offset"]
    v_limit = q["V_int_limit"]
    v_lsb = q["V_lsb"]
    substeps = DELTA_SIGMA_SUBSTEPS
    step = clock / substeps
    decay = exp_q(-step / tau, DYNAMIC_PRECISION)
    threshold = v_threshold + v_offset
    quantum = v_lsb / v_ref

    state = Interval.point(Fraction(0))
    peak = Fraction(0)
    max_width = Fraction(0)
    time = Fraction(0)
    levels: list[int] = []
    trace: list[DynamicTracePoint] = []
    uncertain_count = 0

    for clock_index in range(1, samples + 1):
        before_clock = state
        if before_clock.lo >= threshold:
            level = 1
            uncertain = False
        elif before_clock.hi <= threshold:
            level = 0
            uncertain = False
        else:
            level = 1 if before_clock.midpoint >= threshold else 0
            uncertain = True
            uncertain_count += 1
        feedback = v_ref * level
        levels.append(level)

        for substep in range(1, substeps + 1):
            before = state
            drive = v_in - feedback
            after = _round_outward(drive + (before - drive) * decay)
            time += step
            peak = max(peak, before.abs().hi, after.abs().hi)
            max_width = max(max_width, after.width)
            trace.append(
                DynamicTracePoint(
                    tick=(clock_index - 1) * substeps + substep,
                    input_value=input_value,
                    state_before=before,
                    state_after=after,
                    level=level,
                    feedback=feedback,
                    uncertain=uncertain,
                    time=time,
                )
            )
            state = after

    mean = Fraction(sum(levels), samples)
    mean_error = mean - input_value
    tracking_ok = abs(mean_error) <= quantum
    range_ok = peak <= v_limit
    comparator_ok = uncertain_count == 0
    coverage_ok = len(trace) == samples * substeps
    checks = [
        {
            "name": "continuous-time RC step",
            "status": "pass",
            "detail": (
                "between clock edges the RC state follows the exact "
                "first-order exponential step with constant feedback"
            ),
        },
        {
            "name": "clocked comparator",
            "status": "pass" if comparator_ok else "gap",
            "detail": (
                f"{uncertain_count} uncertain comparator decision(s) at the "
                "declared threshold and offset"
            ),
        },
        {
            "name": "integrator range",
            "status": "pass" if range_ok else "gap",
            "detail": (
                f"continuous peak {_decimal(peak)} V <= declared limit "
                f"{_decimal(v_limit)} V"
            ),
        },
        {
            "name": "sampled-mean tracking",
            "status": "pass" if tracking_ok else "gap",
            "detail": (
                f"mean {mean} ({_decimal(mean)}) vs input {input_value}; "
                f"error {mean_error} <= one LSB {quantum}"
            ),
        },
        {
            "name": "substep coverage",
            "status": "pass" if coverage_ok else "gap",
            "detail": (
                f"{len(trace)} exact substep(s) for {samples} clock(s) x "
                f"{substeps} substep(s)"
            ),
        },
    ]
    status = (
        "pass"
        if range_ok and tracking_ok and comparator_ok and coverage_ok
        else "gap"
    )
    gaps = (
        "The continuous-time transient holds feedback constant within each "
        "clock and uses an ideal comparator; switch resistance, capacitor "
        "leakage, op-amp slew, clock jitter and metastability are not modeled.",
    )
    if status != "pass":
        failed = next(
            (item["name"] for item in checks if item["status"] == "gap"),
            "coverage",
        )
        gaps = gaps + (f"Continuous-time transient gap: {failed}.",)
    return {
        "status": status,
        "model": (
            "continuous-time piecewise-exact RC integrator with clocked "
            "comparator/feedback"
        ),
        "samples": samples,
        "substeps": substeps,
        "metrics": {
            "time_step": step,
            "peak_volts": peak,
            "max_state_width": max_width,
            "mean": mean,
            "mean_error": mean_error,
            "final_state": state,
            "uncertain_decisions": Fraction(uncertain_count),
            "tracking_ok": tracking_ok,
        },
        "checks": checks,
        "gaps": list(gaps),
        "trace": [point.as_dict() for point in trace],
    }


def _log_rate(q: Mapping[str, Any], v_log: Q) -> Interval:
    """Continuous log-node rate; the sign defines the forward-invariant box."""
    return (
        q["I_in"]
        - q["I_s"] * exp_q(v_log / q["V_T"], NONLINEAR_PRECISION)
    ) / q["C_j"]


def _log_output_rate(
    q: Mapping[str, Any], v_log: Q, v_out: Q
) -> Interval:
    """Continuous output-node rate for the same box proof."""
    return (
        q["I_s"] * exp_q(q["G"] * v_log / q["V_T"], NONLINEAR_PRECISION)
        - v_out / q["R_out"]
    ) / q["C_out"]


def _feedback_rate(q: Mapping[str, Any], v_out: Q) -> Interval:
    """Unnormalized feedback-loop residual; its sign drives the box proof."""
    return as_interval(
        q["A"] * (q["V_in"] - q["k"] * v_out * v_out / q["V_ref"])
        - v_out
    )


def _log_state_box(q: Mapping[str, Any]) -> dict[str, Q]:
    """Find a continuous forward-invariant box for the log-domain model.

    The log-node voltage is bounded above by the open-circuit diode voltage,
    and the output by ``R_out`` times the largest antilog current on that
    interval.  The boundary signs are checked with interval arithmetic; a
    failed check is a hard certificate error, not an invented bound.
    """
    v_open = q["V_T"] * log_q(q["I_in"] / q["I_s"], NONLINEAR_PRECISION)
    log_hi = v_open.hi
    margin = q["V_T"] / 1000
    for _ in range(64):
        f_lo = _log_rate(q, Fraction(0))
        f_hi = _log_rate(q, log_hi)
        if f_lo.lo >= 0 and f_hi.hi <= 0:
            break
        log_hi += margin
    else:
        raise CentError(
            ErrorCode.BUDGET_EXHAUSTED,
            "could not certify a bounded log-domain state box",
        )

    i_out_hi = (
        q["I_s"]
        * exp_q(q["G"] * log_hi / q["V_T"], NONLINEAR_PRECISION)
    ).hi
    out_hi = max(q["R_out"] * i_out_hi, _round_outward(q["V_out"]).hi)
    out_margin = max(abs(out_hi), Fraction(1)) / 10**9
    for _ in range(64):
        f_out_lo = _log_output_rate(q, Fraction(0), Fraction(0))
        f_out_hi = _log_output_rate(q, log_hi, out_hi)
        if f_out_lo.lo >= 0 and f_out_hi.hi <= 0:
            break
        out_hi += out_margin
        out_margin *= 2
    else:
        raise CentError(
            ErrorCode.BUDGET_EXHAUSTED,
            "could not certify a bounded log-domain output box",
        )

    return {
        "v_log_lo": Fraction(0),
        "v_log_hi": log_hi,
        "v_out_lo": Fraction(0),
        "v_out_hi": out_hi,
    }


def _log_bounded_state_certificate(
    binding: DeviceBinding,
    trace: tuple[DynamicTracePoint, ...] | list[DynamicTracePoint],
    *,
    box: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Prove the continuous log-domain state stays in a declared box.

    A caller-supplied box is checked without expansion.  That is the explicit
    failure path: a too-small box must return ``gap``, not be silently widened.
    """
    q = {item.symbol: item.value for item in binding.quantities}
    if box is None:
        state_box = _log_state_box(q)
        source = "computed forward-invariant box"
    else:
        state_box = {
            "v_log_lo": Fraction(0),
            "v_log_hi": Fraction(box["v_log_hi"]),
            "v_out_lo": Fraction(0),
            "v_out_hi": Fraction(box["v_out_hi"]),
        }
        source = "caller-supplied box"

    log_lo = state_box["v_log_lo"]
    log_hi = state_box["v_log_hi"]
    out_lo = state_box["v_out_lo"]
    out_hi = state_box["v_out_hi"]
    f_log_lo = _log_rate(q, log_lo)
    f_log_hi = _log_rate(q, log_hi)
    f_out_lo = _log_output_rate(q, log_lo, out_lo)
    f_out_hi = _log_output_rate(q, log_hi, out_hi)
    proof_ok = (
        log_hi > log_lo
        and out_hi > out_lo
        and f_log_lo.lo >= 0
        and f_log_hi.hi <= 0
        and f_out_lo.lo >= 0
        and f_out_hi.hi <= 0
    )

    trace_ok = bool(trace)
    for point in trace:
        if point.aux is None or point.output is None:
            trace_ok = False
            break
        if not (
            log_lo <= point.aux.lo <= point.aux.hi <= log_hi
            and out_lo <= point.output.lo <= point.output.hi <= out_hi
        ):
            trace_ok = False
            break

    status = "pass" if proof_ok and trace_ok else "gap"
    if status == "pass":
        detail = (
            f"forward-invariant box V_log in [0, {_decimal(log_hi)}] V and "
            f"V_out in [0, {_decimal(out_hi)}] V: the boundary rates have "
            "the required signs and every numerical interval is contained"
        )
    else:
        detail = (
            f"box not certified (source: {source}): boundary rates "
            f"f_log(0)={_decimal(f_log_lo.lo)}, "
            f"f_log(hi)={_decimal(f_log_hi.hi)}, "
            f"f_out(0)={_decimal(f_out_lo.lo)}, "
            f"f_out(hi)={_decimal(f_out_hi.hi)}; "
            f"numerical trace contained={trace_ok}"
        )
    return {
        "status": status,
        "method": "continuous forward-invariance on a declared state box",
        "source": source,
        "box": state_box,
        "boundary": {
            "f_log_lo": f_log_lo,
            "f_log_hi": f_log_hi,
            "f_out_lo": f_out_lo,
            "f_out_hi": f_out_hi,
        },
        "trace_contained": trace_ok,
        "detail": detail,
    }


def _feedback_state_box(q: Mapping[str, Any]) -> dict[str, Q]:
    """Find a forward-invariant box for the slope-normalized loop."""
    target = _round_outward(q["V_out"])
    v_hi = target.hi
    margin = max(abs(v_hi), Fraction(1)) / 10**6
    for _ in range(64):
        f_lo = _feedback_rate(q, Fraction(0))
        f_hi = _feedback_rate(q, v_hi)
        if f_lo.lo >= 0 and f_hi.hi <= 0:
            break
        v_hi += margin
        margin *= 2
    else:
        raise CentError(
            ErrorCode.BUDGET_EXHAUSTED,
            "could not certify a bounded feedback state box",
        )
    return {"v_lo": Fraction(0), "v_hi": v_hi}


def _feedback_bounded_state_certificate(
    binding: DeviceBinding,
    trace: tuple[DynamicTracePoint, ...] | list[DynamicTracePoint],
    *,
    box: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Prove the continuous quadratic loop stays between 0 and its box top."""
    q = {item.symbol: item.value for item in binding.quantities}
    if box is None:
        state_box = _feedback_state_box(q)
        source = "computed forward-invariant box"
    else:
        state_box = {
            "v_lo": Fraction(0),
            "v_hi": Fraction(box["v_hi"]),
        }
        source = "caller-supplied box"

    v_lo = state_box["v_lo"]
    v_hi = state_box["v_hi"]
    f_lo = _feedback_rate(q, v_lo)
    f_hi = _feedback_rate(q, v_hi)
    proof_ok = (
        v_hi > v_lo and f_lo.lo >= 0 and f_hi.hi <= 0
    )

    trace_ok = bool(trace)
    for point in trace:
        if point.output is None:
            trace_ok = False
            break
        if not (v_lo <= point.output.lo <= point.output.hi <= v_hi):
            trace_ok = False
            break

    status = "pass" if proof_ok and trace_ok else "gap"
    if status == "pass":
        detail = (
            f"forward-invariant box V_out in [0, {_decimal(v_hi)}] V: "
            "f(0) >= 0, f(hi) <= 0, and every numerical interval is contained"
        )
    else:
        detail = (
            f"box not certified (source: {source}): "
            f"f(0)={_decimal(f_lo.lo)}, f(hi)={_decimal(f_hi.hi)}; "
            f"numerical trace contained={trace_ok}"
        )
    return {
        "status": status,
        "method": "continuous forward-invariance on a declared state box",
        "source": source,
        "box": state_box,
        "boundary": {"f_lo": f_lo, "f_hi": f_hi},
        "trace_contained": trace_ok,
        "detail": detail,
    }


def _log_lipschitz(q: Mapping[str, Any], box: Mapping[str, Any]) -> Q:
    """Row-sum Lipschitz bound over the certified log-domain box."""
    v_hi = box["v_log_hi"]
    exp_log = exp_q(v_hi / q["V_T"], NONLINEAR_PRECISION)
    exp_out = exp_q(q["G"] * v_hi / q["V_T"], NONLINEAR_PRECISION)
    j11 = q["I_s"] * exp_log.hi / (q["V_T"] * q["C_j"])
    j21 = (
        q["I_s"] * q["G"] * exp_out.hi
        / (q["V_T"] * q["C_out"])
    )
    j22 = 1 / (q["R_out"] * q["C_out"])
    return max(j11, j21 + j22)


def _feedback_lipschitz(q: Mapping[str, Any], box: Mapping[str, Any]) -> Q:
    """Interval derivative bound for the slope-normalized feedback loop."""
    derivative = _feedback_derivative_interval(
        q, Interval(Fraction(0), box["v_hi"])
    )
    return max(abs(derivative.lo), abs(derivative.hi))


def _feedback_derivative_negative(
    q: Mapping[str, Any],
    box: Mapping[str, Any],
    *,
    cells: int = NONLINEAR_GRID,
) -> bool:
    """Certify a negative scalar derivative by exact interval subdivision.

    The full-box interval evaluation overestimates the derivative because the
    numerator and denominator are treated independently.  Splitting the box into
    small rational cells removes enough of that dependency to certify the sign
    for the declared flow; any unresolved cell returns ``False``.
    """
    lo = box["v_lo"]
    hi = box["v_hi"]
    for index in range(cells):
        left = lo + (hi - lo) * Fraction(index, cells)
        right = lo + (hi - lo) * Fraction(index + 1, cells)
        derivative = _feedback_derivative_interval(q, Interval(left, right))
        if derivative.hi >= 0:
            return False
    return True


def _log_stability_certificate(
    q: Mapping[str, Any],
    box: Mapping[str, Any],
) -> dict[str, Any]:
    """Prove the monotone two-node flow converges inside its state box."""
    log_lo = box["v_log_lo"]
    log_hi = box["v_log_hi"]
    out_lo = box["v_out_lo"]
    out_hi = box["v_out_hi"]
    f_log_lo = _log_rate(q, log_lo)
    f_log_hi = _log_rate(q, log_hi)
    f_out_lo = _log_output_rate(q, log_lo, out_lo)
    f_out_hi = _log_output_rate(q, log_hi, out_hi)
    exp_log = Interval(log_lo, log_hi).exp(NONLINEAR_PRECISION)
    j11 = -q["I_s"] * exp_log / (q["V_T"] * q["C_j"])
    cross = _log_cross_lipschitz(q, box)
    decay = 1 / (q["R_out"] * q["C_out"])
    proof = (
        f_log_lo.lo >= 0
        and f_log_hi.hi <= 0
        and f_out_lo.lo >= 0
        and f_out_hi.hi <= 0
        and j11.hi < 0
        and cross > 0
        and decay > 0
    )
    return {
        "status": "pass" if proof else "gap",
        "method": "monotone triangular flow on the forward-invariant box",
        "box": box,
        "boundary": {
            "f_log_lo": f_log_lo,
            "f_log_hi": f_log_hi,
            "f_out_lo": f_out_lo,
            "f_out_hi": f_out_hi,
        },
        "derivative_signs": {
            "log_self": _round_outward(j11),
            "output_self": _round_up(-decay, 12),
            "log_to_output": _round_up(cross, 12),
        },
        "detail": (
            "log-node and output-node boundary rates point inward; the "
            "log-node self-derivative is negative and the output self-derivative "
            "is negative with a positive log-to-output coupling, so the "
            "declared triangular flow has a unique attracting equilibrium in "
            "the box"
            if proof
            else "the monotone triangular stability signs are not all certified"
        ),
    }


def _feedback_stability_certificate(
    q: Mapping[str, Any],
    box: Mapping[str, Any],
) -> dict[str, Any]:
    """Prove the scalar slope-normalized loop is a stable gradient flow."""
    lo = box["v_lo"]
    hi = box["v_hi"]
    f_lo = _feedback_rate(q, lo)
    f_hi = _feedback_rate(q, hi)
    derivative_negative = _feedback_derivative_negative(q, box)
    proof = f_lo.lo >= 0 and f_hi.hi <= 0 and derivative_negative
    return {
        "status": "pass" if proof else "gap",
        "method": "negative scalar derivative on a subdivided invariant box",
        "box": box,
        "boundary": {"f_lo": f_lo, "f_hi": f_hi},
        "derivative_negative": derivative_negative,
        "detail": (
            "f(0) >= 0, f(hi) <= 0 and the derivative is certified negative "
            "on every rational subinterval, so the scalar flow has a unique "
            "stable equilibrium in the box"
            if proof
            else "the scalar stability signs or negative derivative are not certified"
        ),
    }


def _max_abs_interval(value: Interval) -> Q:
    return max(abs(value.lo), abs(value.hi))


def _log_cross_lipschitz(q: Mapping[str, Any], box: Mapping[str, Any]) -> Q:
    """Bound the log-node to output-node coupling over the state box."""
    exp_out = exp_q(q["G"] * box["v_log_hi"] / q["V_T"], NONLINEAR_PRECISION)
    return q["I_s"] * q["G"] * exp_out.hi / (q["V_T"] * q["C_out"])


def _log_second_derivative_bound(
    q: Mapping[str, Any],
    box: Mapping[str, Any],
) -> tuple[Q, Q]:
    """Certified bounds on |V_log''| and |V_out''| over a state box."""
    v = Interval(box["v_log_lo"], box["v_log_hi"])
    out = Interval(box["v_out_lo"], box["v_out_hi"])
    exp_log = (v / q["V_T"]).exp(NONLINEAR_PRECISION)
    exp_out = (q["G"] * v / q["V_T"]).exp(NONLINEAR_PRECISION)
    f_log = (q["I_in"] - q["I_s"] * exp_log) / q["C_j"]
    f_out = (q["I_s"] * exp_out - out / q["R_out"]) / q["C_out"]
    j11 = -q["I_s"] * exp_log / (q["V_T"] * q["C_j"])
    j21 = q["I_s"] * q["G"] * exp_out / (q["V_T"] * q["C_out"])
    j22 = -1 / (q["R_out"] * q["C_out"])
    return (
        _max_abs_interval(j11 * f_log),
        _max_abs_interval(j21 * f_log + j22 * f_out),
    )


def _feedback_rate_interval(q: Mapping[str, Any], v: Interval) -> Interval:
    residual = q["A"] * (q["V_in"] - q["k"] * v * v / q["V_ref"]) - v
    slope = 1 + 2 * q["A"] * q["k"] * v / q["V_ref"]
    return residual / (q["tau_cl"] * slope)


def _feedback_derivative_interval(q: Mapping[str, Any], v: Interval) -> Interval:
    residual = q["A"] * (q["V_in"] - q["k"] * v * v / q["V_ref"]) - v
    slope = 1 + 2 * q["A"] * q["k"] * v / q["V_ref"]
    residual_prime = -2 * q["A"] * q["k"] * v / q["V_ref"] - 1
    slope_prime = 2 * q["A"] * q["k"] / q["V_ref"]
    return (
        residual_prime * slope - residual * slope_prime
    ) / (q["tau_cl"] * slope * slope)


def _feedback_second_derivative_bound(
    q: Mapping[str, Any],
    box: Mapping[str, Any],
) -> Q:
    v = Interval(box["v_lo"], box["v_hi"])
    return _max_abs_interval(
        _feedback_derivative_interval(q, v) * _feedback_rate_interval(q, v)
    )


def _global_error_envelope(
    route_key: str,
    q: Mapping[str, Any],
    box: Mapping[str, Any],
    stats: Mapping[str, Any],
    *,
    proof_box: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a certified global error bound from local truncation terms.

    The local term is the backward-Euler bound ``h^2 M2 / 2`` over a box that
    contains the exact solution during the step.  The log route uses its
    triangular contraction; the feedback route uses the negative derivative
    of the scalar flow.  If the required sign or truncation callback is absent,
    the old step-doubling envelope is retained as an explicit conditional
    fallback.
    """
    proof = dict(proof_box or box)
    local_defect = stats["local_defect_sum"]
    local_sums = tuple(stats.get("local_truncation_sums", ()))
    widths = tuple(stats.get("max_state_widths", ()))
    local_truncation_sum = sum(local_sums, Fraction(0))

    if route_key == "sqrt-log" and len(local_sums) == 2 and len(widths) == 2:
        first = local_sums[0] + widths[0]
        cross = _log_cross_lipschitz(q, proof)
        decay = 1 / (q["R_out"] * q["C_out"])
        second = local_sums[1] + widths[1] + (cross / decay) * first
        envelope = _round_up(second)
        within_target = envelope <= CERTIFICATE_ERROR_TARGET
        return {
            "status": "pass" if within_target else "gap",
            "method": "certified local truncation + triangular contraction",
            "certified": True,
            "lipschitz_bound": None,
            "time_horizon": 12 * q["tau_out"],
            "exponent": None,
            "local_defect_sum": local_defect,
            "local_truncation_sum": local_truncation_sum,
            "local_truncation_components": list(local_sums),
            "interval_widths": list(widths),
            "state_bound": _round_up(first),
            "envelope": envelope,
            "target": CERTIFICATE_ERROR_TARGET,
            "within_target": within_target,
            "detail": (
                f"certified backward-Euler local truncation h^2 M2/2 and "
                f"triangular contraction: state bound {_decimal(_round_up(first))} V, "
                f"output bound {_decimal(envelope)} V; target "
                f"{_decimal(CERTIFICATE_ERROR_TARGET)} V is "
                f"{'met' if within_target else 'exceeded'}."
            ),
        }

    if route_key == "sqrt-feedback" and len(local_sums) == 1 and len(widths) == 1:
        if _feedback_derivative_negative(q, proof):
            envelope = _round_up(local_sums[0] + widths[0])
            within_target = envelope <= CERTIFICATE_ERROR_TARGET
            return {
                "status": "pass" if within_target else "gap",
                "method": "certified local truncation + negative scalar derivative",
                "certified": True,
                "lipschitz_bound": None,
                "time_horizon": 12 * q["tau_cl"],
                "exponent": None,
                "local_defect_sum": local_defect,
                "local_truncation_sum": local_truncation_sum,
                "local_truncation_components": list(local_sums),
                "interval_widths": list(widths),
                "state_bound": envelope,
                "envelope": envelope,
                "target": CERTIFICATE_ERROR_TARGET,
                "within_target": within_target,
                "detail": (
                    f"certified backward-Euler local truncation h^2 M2/2 and "
                    f"a strictly negative scalar derivative over the certified "
                    f"box: output bound {_decimal(envelope)} V; target "
                    f"{_decimal(CERTIFICATE_ERROR_TARGET)} V is "
                    f"{'met' if within_target else 'exceeded'}."
                ),
            }

    if route_key == "sqrt-log":
        lipschitz = _round_up(_log_lipschitz(q, box))
        horizon = 12 * q["tau_out"]
    elif route_key == "sqrt-feedback":
        lipschitz = _round_up(_feedback_lipschitz(q, box))
        horizon = 12 * q["tau_cl"]
    else:
        raise CentError(
            ErrorCode.VALIDATION_ERROR,
            f"no global envelope for route {route_key!r}",
        )

    exponent = _round_up(lipschitz * horizon)
    if exponent > CERTIFICATE_GRONWALL_LIMIT:
        envelope = None
        within_target = False
        detail = (
            f"global error remains conditional: the Gronwall exponent "
            f"L*T={_decimal(exponent)} exceeds the declared envelope limit "
            f"{CERTIFICATE_GRONWALL_LIMIT}; local defect sum "
            f"{_decimal(local_defect)} is a step-doubling estimate, not a "
            "certified local error bound."
        )
    else:
        envelope = _round_up(
            local_defect * exp_q(exponent, NONLINEAR_PRECISION).hi
        )
        within_target = envelope <= CERTIFICATE_ERROR_TARGET
        detail = (
            f"conditional Gronwall envelope {_decimal(envelope)} V from "
            f"L={_decimal(lipschitz)} and local defect sum "
            f"{_decimal(local_defect)}; the local term is a step-doubling "
            "estimate, not a certified local error bound."
        )

    return {
        "status": "gap",
        "method": "Gronwall envelope from step-doubling defect (conditional)",
        "certified": False,
        "lipschitz_bound": lipschitz,
        "time_horizon": horizon,
        "exponent": exponent,
        "local_defect_sum": local_defect,
        "local_truncation_sum": local_truncation_sum if local_sums else None,
        "local_truncation_components": list(local_sums) if local_sums else None,
        "interval_widths": list(widths) if widths else None,
        "envelope": envelope,
        "target": CERTIFICATE_ERROR_TARGET,
        "within_target": within_target,
        "detail": detail,
    }


def _log_dynamic(
    binding: DeviceBinding,
    *,
    samples: int,
    selected_option: str,
    certificate_box: Mapping[str, Q] | None = None,
) -> DynamicResult:
    """Run the two-node nonlinear diode/load ODE with adaptive backward Euler."""
    q = {item.symbol: item.value for item in binding.quantities}
    target = _round_outward(q["V_out"])
    tau_slow = q["tau_out"]
    t_final = 12 * tau_slow
    v_open = _midpoint(
        q["V_T"] * log_q(q["I_in"] / q["I_s"], NONLINEAR_PRECISION)
    )

    def log_step(state, h):
        v_log, v_out = state
        old_log = v_log.midpoint
        c_term = q["C_j"] / h

        def log_equation(value):
            return (
                c_term * (value - old_log)
                + q["I_s"]
                * exp_q(
                    value / q["V_T"],
                    NONLINEAR_PRECISION,
                    round_places=NONLINEAR_ROUND,
                )
                - q["I_in"]
            )

        # The backward-Euler root lies between the previous state and the
        # open-circuit diode voltage; the capacitor term makes it bracketed.
        lo = old_log
        if _midpoint(log_equation(lo)) > 0:
            lo -= 2 * q["V_T"]
            for _ in range(16):
                if _midpoint(log_equation(lo)) <= 0:
                    break
                lo -= 2 * q["V_T"]
            else:
                raise CentError(
                    ErrorCode.DOMAIN_ERROR,
                    "could not bracket the log-node equation below",
                )
        hi = v_open + 2 * q["V_T"]
        if _midpoint(log_equation(hi)) < 0:
            for _ in range(16):
                hi += 2 * q["V_T"]
                if _midpoint(log_equation(hi)) >= 0:
                    break
            else:
                raise CentError(
                    ErrorCode.DOMAIN_ERROR,
                    "could not bracket the log-node equation above",
                )
        new_log = _bisect_increasing(
            log_equation, lo, hi, places=NONLINEAR_GRID
        )
        i_out = q["I_s"] * (
            q["G"] * new_log / q["V_T"]
        ).exp(NONLINEAR_PRECISION, round_places=NONLINEAR_ROUND)
        new_out = (
            v_out + h * i_out / q["C_out"]
        ) / (1 + h / (q["R_out"] * q["C_out"]))
        return (_round_outward(new_log), _round_outward(new_out))

    def log_error(fine, coarse):
        return max(
            _scaled_step_error(
                fine[0], coarse[0], ADAPTIVE_ATOL_LOG, ADAPTIVE_RTOL
            ),
            _scaled_step_error(
                fine[1], coarse[1], ADAPTIVE_ATOL_OUT, ADAPTIVE_RTOL
            ),
        )

    proof_box = _log_state_box(q)
    proof_second = _log_second_derivative_bound(q, proof_box)

    def log_local_truncation(state, h):
        factor = h * h / 2
        return (
            _round_up(factor * proof_second[0]),
            _round_up(factor * proof_second[1]),
        )

    h0 = min(t_final / (4 * samples), q["tau_log"] / 8)
    states, stats = _adaptive_integrate(
        log_step,
        (Interval.point(Fraction(0)), Interval.point(Fraction(0))),
        t_final=t_final,
        samples=samples,
        error=log_error,
        h0=h0,
        h_max=tau_slow,
        local_truncation=log_local_truncation,
    )

    trace: list[DynamicTracePoint] = []
    previous: Interval | None = None
    monotonic = True
    range_ok = True
    final_error = Fraction(1)
    for index, (when, state) in enumerate(states, 1):
        v_log, v_out = state
        output = _round_outward(v_out)
        if previous is not None and output.lo + Fraction(1, 10**9) < previous.lo:
            monotonic = False
        if output.hi > q["V_supply"]:
            range_ok = False
        final_error = (
            (target - output).abs().hi / target.midpoint
            if target.midpoint > 0
            else Fraction(1)
        )
        trace.append(
            DynamicTracePoint(
                tick=index,
                input_value=binding.input_value,
                time=when,
                output=output,
                target=target,
                aux=_round_outward(v_log),
            )
        )
        previous = output

    if "C_j" in q:
        bounded = _log_bounded_state_certificate(
            binding, trace, box=certificate_box
        )
        global_cert = _global_error_envelope(
            "sqrt-log", q, bounded["box"], stats, proof_box=proof_box
        )
    else:
        bounded = _feedback_bounded_state_certificate(
            binding, trace, box=certificate_box
        )
        global_cert = _global_error_envelope(
            "sqrt-feedback", q, bounded["box"], stats, proof_box=proof_box
        )
    stability = _display_certificate(
        _log_stability_certificate(q, proof_box)
        if "C_j" in q
        else _feedback_stability_certificate(q, proof_box)
    )
    bounded = _display_certificate(bounded)
    certificates = {
        "bounded_state": bounded,
        "global_error": global_cert,
        "stability": stability,
    }

    settling_ok = final_error <= Fraction(1, 100)
    status = (
        "partial"
        if settling_ok
        and monotonic
        and range_ok
        and bounded["status"] == "pass"
        and stability["status"] == "pass"
        else "gap"
    )
    checks = (
        DynamicCheck(
            "nonlinear ODE state",
            "pass",
            "V_log and V_out are integrated as exact interval states through the "
            "diode and output-load equations",
            stats["accepted_steps"],
        ),
        DynamicCheck(
            "large-signal settling",
            "pass" if settling_ok else "gap",
            f"final relative error {_decimal(final_error)} <= 1/100",
            final_error,
        ),
        DynamicCheck(
            "monotonic output",
            "pass" if monotonic else "gap",
            "the nonlinear output remains nondecreasing at the declared step",
            Fraction(1) if monotonic else Fraction(0),
        ),
        DynamicCheck(
            "output range",
            "pass" if range_ok else "gap",
            f"output peak {_decimal(trace[-1].output.hi)} V <= supply {q['V_supply']} V",
            trace[-1].output,
        ),
        DynamicCheck(
            "adaptive step control",
            "pass",
            f"{int(stats['accepted_steps'])} accepted / "
            f"{int(stats['rejected_steps'])} rejected step(s); max normalized "
            f"step-doubling error {_decimal(stats['max_local_error_ratio'])} "
            f"<= 1; step range {_decimal(stats['min_step'])}.."
            f"{_decimal(stats['max_step'])} s; local estimate only",
            stats["max_local_error_ratio"],
        ),
        DynamicCheck(
            "bounded-state certificate",
            bounded["status"],
            bounded["detail"],
            bounded["box"],
        ),
        DynamicCheck(
            "large-signal stability",
            stability["status"],
            stability["detail"],
            stability["box"],
        ),
        DynamicCheck(
            "global error envelope",
            global_cert["status"],
            global_cert["detail"],
            global_cert["exponent"],
        ),
    )
    gaps = (
        f"Bounded-state certificate: {bounded['detail']}. "
        f"Stability certificate: {stability['detail']}. "
        f"Global error envelope: {global_cert['detail']}",
        "C_j and C_out are declared reference capacitances, not measured diode "
        "or board parasitics. Buffer pole, bias-network bandwidth and "
        "saturation recovery are absent.",
        "No thermal drift, 1/f noise, measured diode model or fabrication "
        "evidence is attached.",
    )
    transient_ok = settling_ok and monotonic and range_ok
    nonlinear_transient = {
        "status": "pass" if transient_ok else "gap",
        "model": (
            "nonlinear large-signal two-node diode/load adaptive "
            "backward-Euler transient"
        ),
        "samples": len(trace),
        "steps": stats["accepted_steps"],
        "trace_source": "route trace",
        "checks": [
            {
                "name": "nonlinear transient",
                "status": "pass" if transient_ok else "gap",
                "detail": "settling, monotonicity and output-range checks",
            }
        ],
        "gaps": [] if transient_ok else [
            "The nonlinear route transient did not pass its settling, "
            "monotonicity or output-range check."
        ],
    }
    return DynamicResult(
        route_key="sqrt-log",
        route_id=binding.route_id,
        route_name=binding.name,
        model=(
            "nonlinear large-signal two-node diode/load adaptive "
            "backward-Euler transient"
        ),
        samples=samples,
        input_value=binding.input_value,
        selected_option=selected_option,
        status=status,
        metrics={
            "tau_log": q["tau_log"],
            "tau_out": tau_slow,
            "integration_steps": stats["accepted_steps"],
            "rejected_steps": stats["rejected_steps"],
            "min_step_seconds": stats["min_step"],
            "max_step_seconds": stats["max_step"],
            "max_local_error_ratio": stats["max_local_error_ratio"],
            "max_rejected_error_ratio": stats["max_rejected_error_ratio"],
            "local_defect_sum": stats["local_defect_sum"],
            "bounded_state_status": bounded["status"],
            "global_error_status": global_cert["status"],
            "global_lipschitz_bound": global_cert["lipschitz_bound"],
            "global_envelope_exponent": global_cert["exponent"],
            "local_atol": ADAPTIVE_ATOL_OUT,
            "local_rtol": ADAPTIVE_RTOL,
            "final_relative_error": final_error,
            "target_volts": target,
            "v_log_final": trace[-1].aux,
            "v_out_final": trace[-1].output,
        },
        checks=checks,
        trace=tuple(trace),
        gaps=gaps,
        certificates=certificates,
        nonlinear_transient=nonlinear_transient,
    )


def _feedback_dynamic(
    binding: DeviceBinding,
    *,
    samples: int,
    selected_option: str,
    certificate_box: Mapping[str, Q] | None = None,
) -> DynamicResult:
    """Run the nonlinear quadratic closed-loop ODE with adaptive backward Euler.

    ``tau_cl`` is declared as the small-signal closed-loop pole.  The raw loop
    residual ``A*(V_in - k*V^2/V_ref) - V`` would make the closed-loop
    linearization ``tau_cl/(1 + 2*A*k*V/V_ref)``, roughly four orders of
    magnitude faster than the declared pole.  Dividing the residual by its
    local slope keeps the equilibrium and the nonlinear quadratic term, but
    makes the linearization exactly ``dV/dt = -dV/tau_cl`` at every operating
    point.
    """
    q = {item.symbol: item.value for item in binding.quantities}
    target = _round_outward(q["V_out"])
    tau_cl = q["tau_cl"]
    t_final = 12 * tau_cl

    def feedback_step(state, h):
        old_out = state[0]
        ratio = h / tau_cl

        # Backward Euler turns the slope-normalized quadratic loop into
        #   a*V^2 + b*V - (V_old + ratio*A*V_in) = 0
        # with a = A*k*(2 + ratio)/V_ref and b = 1 + ratio - 2*A*k*V_old/V_ref.
        # The constant term is negative, so the physical root is the unique
        # positive quadratic root; solving it directly avoids bracketing the
        # wrong (negative) root.
        a = q["A"] * q["k"] * (2 + ratio) / q["V_ref"]
        b = 1 + ratio - 2 * q["A"] * q["k"] * old_out / q["V_ref"]
        disc = b * b + 4 * a * (old_out + ratio * q["A"] * q["V_in"])
        if disc.lo <= 0:
            raise CentError(
                ErrorCode.DOMAIN_ERROR,
                "dynamic feedback discriminant is not positive",
            )
        sqrt_lo = sqrt_q(disc.lo, NONLINEAR_PRECISION)
        sqrt_hi = sqrt_q(disc.hi, NONLINEAR_PRECISION)
        sqrt_disc = Interval(sqrt_lo.lo, sqrt_hi.hi)
        return (_round_outward((sqrt_disc - b) / (2 * a)),)

    def feedback_error(fine, coarse):
        return _scaled_step_error(
            fine[0], coarse[0], ADAPTIVE_ATOL_OUT, ADAPTIVE_RTOL
        )

    proof_box = _feedback_state_box(q)
    proof_second = _feedback_second_derivative_bound(q, proof_box)

    def feedback_local_truncation(state, h):
        return (_round_up(h * h * proof_second / 2),)

    h0 = min(t_final / (4 * samples), tau_cl / 16)
    states, stats = _adaptive_integrate(
        feedback_step,
        (Interval.point(Fraction(0)),),
        t_final=t_final,
        samples=samples,
        error=feedback_error,
        h0=h0,
        h_max=tau_cl,
        local_truncation=feedback_local_truncation,
    )

    trace: list[DynamicTracePoint] = []
    previous: Interval | None = None
    monotonic = True
    range_ok = True
    final_error = Fraction(1)
    for index, (when, state) in enumerate(states, 1):
        output = _round_outward(state[0])
        if previous is not None and output.lo + Fraction(1, 10**9) < previous.lo:
            monotonic = False
        if output.hi > q["V_supply"]:
            range_ok = False
        final_error = (
            (target - output).abs().hi / target.midpoint
            if target.midpoint > 0
            else Fraction(1)
        )
        trace.append(
            DynamicTracePoint(
                tick=index,
                input_value=binding.input_value,
                time=when,
                output=output,
                target=target,
            )
        )
        previous = output

    if "C_j" in q:
        bounded = _log_bounded_state_certificate(
            binding, trace, box=certificate_box
        )
        global_cert = _global_error_envelope(
            "sqrt-log", q, bounded["box"], stats, proof_box=proof_box
        )
    else:
        bounded = _feedback_bounded_state_certificate(
            binding, trace, box=certificate_box
        )
        global_cert = _global_error_envelope(
            "sqrt-feedback", q, bounded["box"], stats, proof_box=proof_box
        )
    stability = _display_certificate(
        _log_stability_certificate(q, proof_box)
        if "C_j" in q
        else _feedback_stability_certificate(q, proof_box)
    )
    bounded = _display_certificate(bounded)
    certificates = {
        "bounded_state": bounded,
        "global_error": global_cert,
        "stability": stability,
    }

    settling_ok = final_error <= Fraction(1, 100)
    status = (
        "partial"
        if settling_ok
        and monotonic
        and range_ok
        and bounded["status"] == "pass"
        and stability["status"] == "pass"
        else "gap"
    )
    checks = (
        DynamicCheck(
            "nonlinear closed-loop ODE",
            "pass",
            "the quadratic multiplier feedback loop is integrated as exact "
            "interval states with tau_cl normalized to the declared "
            "small-signal pole",
            stats["accepted_steps"],
        ),
        DynamicCheck(
            "large-signal settling",
            "pass" if settling_ok else "gap",
            f"final relative error {_decimal(final_error)} <= 1/100",
            final_error,
        ),
        DynamicCheck(
            "monotonic output",
            "pass" if monotonic else "gap",
            "the nonlinear output remains nondecreasing at the declared step",
            Fraction(1) if monotonic else Fraction(0),
        ),
        DynamicCheck(
            "output range",
            "pass" if range_ok else "gap",
            f"output peak {_decimal(trace[-1].output.hi)} V <= supply {q['V_supply']} V",
            trace[-1].output,
        ),
        DynamicCheck(
            "adaptive step control",
            "pass",
            f"{int(stats['accepted_steps'])} accepted / "
            f"{int(stats['rejected_steps'])} rejected step(s); max normalized "
            f"step-doubling error {_decimal(stats['max_local_error_ratio'])} "
            f"<= 1; step range {_decimal(stats['min_step'])}.."
            f"{_decimal(stats['max_step'])} s; local estimate only",
            stats["max_local_error_ratio"],
        ),
        DynamicCheck(
            "bounded-state certificate",
            bounded["status"],
            bounded["detail"],
            bounded["box"],
        ),
        DynamicCheck(
            "large-signal stability",
            stability["status"],
            stability["detail"],
            stability["box"],
        ),
        DynamicCheck(
            "global error envelope",
            global_cert["status"],
            global_cert["detail"],
            global_cert["exponent"],
        ),
    )
    gaps = (
        f"Bounded-state certificate: {bounded['detail']}. "
        f"Stability certificate: {stability['detail']}. "
        f"Global error envelope: {global_cert['detail']}",
        "The declared output-load pole R_out*C_out is reported but not "
        "separately integrated; the loop uses the declared tau_cl.",
        "tau_cl is a declared reference closed-loop pole, not a measured "
        "op-amp/multiplier pole. Slew, noise and offset drift are "
        "not modeled.",
    )
    transient_ok = settling_ok and monotonic and range_ok
    nonlinear_transient = {
        "status": "pass" if transient_ok else "gap",
        "model": (
            "nonlinear large-signal quadratic closed-loop adaptive "
            "backward-Euler transient with declared small-signal pole"
        ),
        "samples": len(trace),
        "steps": stats["accepted_steps"],
        "trace_source": "route trace",
        "checks": [
            {
                "name": "nonlinear transient",
                "status": "pass" if transient_ok else "gap",
                "detail": "settling, monotonicity and output-range checks",
            }
        ],
        "gaps": [] if transient_ok else [
            "The nonlinear route transient did not pass its settling, "
            "monotonicity or output-range check."
        ],
    }
    return DynamicResult(
        route_key="sqrt-feedback",
        route_id=binding.route_id,
        route_name=binding.name,
        model=(
            "nonlinear large-signal quadratic closed-loop adaptive "
            "backward-Euler transient with declared small-signal pole"
        ),
        samples=samples,
        input_value=binding.input_value,
        selected_option=selected_option,
        status=status,
        metrics={
            "tau_cl": tau_cl,
            "tau_out": q["tau_out"],
            "integration_steps": stats["accepted_steps"],
            "rejected_steps": stats["rejected_steps"],
            "min_step_seconds": stats["min_step"],
            "max_step_seconds": stats["max_step"],
            "max_local_error_ratio": stats["max_local_error_ratio"],
            "max_rejected_error_ratio": stats["max_rejected_error_ratio"],
            "local_defect_sum": stats["local_defect_sum"],
            "bounded_state_status": bounded["status"],
            "global_error_status": global_cert["status"],
            "global_lipschitz_bound": global_cert["lipschitz_bound"],
            "global_envelope_exponent": global_cert["exponent"],
            "local_atol": ADAPTIVE_ATOL_OUT,
            "local_rtol": ADAPTIVE_RTOL,
            "final_relative_error": final_error,
            "target_volts": target,
            "v_out_final": trace[-1].output,
        },
        checks=checks,
        trace=tuple(trace),
        gaps=gaps,
        certificates=certificates,
        nonlinear_transient=nonlinear_transient,
    )


def _unsupported_dynamic(
    result: DesignResult,
    *,
    samples: int,
) -> DynamicResult:
    """Return explicit coverage gaps when a route has no dynamic quantities."""
    binding = result.selected.binding
    assert binding is not None
    if result.route_name == "sqrt-log":
        missing = (
            "junction capacitance",
            "output load capacitance",
            "junction bias network bandwidth",
        )
    else:
        missing = (
            "error-amplifier gain-bandwidth",
            "multiplier bandwidth",
            "output load capacitance",
        )
    detail = (
        "no declared dynamic quantities for " + ", ".join(missing)
        + "; static binding alone cannot define a time-domain model"
    )
    return DynamicResult(
        route_key=result.route_name,
        route_id=binding.route_id,
        route_name=result.space.name,
        model="not declared",
        samples=samples,
        input_value=binding.input_value,
        selected_option=result.selected.option.name,
        status="gap",
        metrics={},
        checks=(DynamicCheck("declared dynamic model", "gap", detail),),
        trace=(),
        gaps=(
            "This route has no declared capacitance, load pole or finite "
            "bandwidth in its device binding. No dynamic trajectory was "
            "invented.",
            "Add declared dynamic parameters and a device-law transient model "
            "before claiming settling, bandwidth or stability for this route.",
        ),
    )


def analyze_design(
    result: DesignResult,
    *,
    samples: Any = DEFAULT_SAMPLES,
    certificate_box: Mapping[str, Any] | None = None,
) -> DynamicResult:
    """Run the declared dynamic model for a solved design.

    The delta-sigma route uses its sampled RC/clock loop; the two compute routes
    use nonlinear large-signal backward-Euler transients.  A route without
    declared timing quantities still returns an explicit gap rather than a
    fabricated transient.
    """
    count = _validate_samples(samples)
    if result.selected is None or result.selected.binding is None:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            "no declared design is selected; no dynamic model can be run",
        )
    binding = result.selected.binding
    box = _validate_certificate_box(result.route_name, certificate_box)
    if result.route_name == "delta-sigma":
        return _delta_sigma_dynamic(
            binding,
            samples=count,
            selected_option=result.selected.option.name,
        )
    if result.route_name == "sqrt-log":
        return _log_dynamic(
            binding,
            samples=count,
            selected_option=result.selected.option.name,
            certificate_box=box,
        )
    if result.route_name == "sqrt-feedback":
        return _feedback_dynamic(
            binding,
            samples=count,
            selected_option=result.selected.option.name,
            certificate_box=box,
        )
    return _unsupported_dynamic(result, samples=count)


def simulate_route(
    route_name: str,
    *,
    input_value: Any | None = None,
    input_min: Any | None = None,
    input_max: Any | None = None,
    accuracy: Any = "1/100",
    max_cost: Any | None = None,
    min_bandwidth: Any | None = None,
    samples: Any = DEFAULT_SAMPLES,
    certificate_box: Mapping[str, Any] | None = None,
) -> DynamicResult:
    """Solve the declared design and run its available dynamic model."""
    result = solve_route(
        route_name,
        input_value=input_value,
        input_min=input_min,
        input_max=input_max,
        accuracy=accuracy,
        max_cost=max_cost,
        min_bandwidth=min_bandwidth,
    )
    return analyze_design(
        result, samples=samples, certificate_box=certificate_box
    )


__all__ = [
    "CERTIFICATE_BOX_KEYS",
    "DEFAULT_SAMPLES",
    "DynamicCheck",
    "DynamicResult",
    "DynamicTracePoint",
    "MAX_SAMPLES",
    "SCHEMA",
    "analyze_design",
    "simulate_route",
]
