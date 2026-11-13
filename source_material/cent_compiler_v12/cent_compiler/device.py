"""Declared device bindings for the exact routes.

This layer is deliberately smaller than a fabrication netlist.  It maps the
normalized route variables onto concrete electrical quantities, checks the
declared device laws exactly, and reports a conservative worst-case error
budget.  The numbers are reference-design specifications, not datasheet values
or measurements.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping

from .assembly import (
    delta_sigma_route,
    kcl_sum_route,
    log_domain_sqrt_route,
    opamp_multiplier_sqrt_route,
)
from .exact import CentError, ErrorCode, Q, q, q_to_json
from .interval import Interval, exp_q, log_q, sqrt_q

SCHEMA = "cent-device/1"

# Exact SI definitions.  The thermal voltage is a declared operating-point
# quantity, not a measured device parameter.
BOLTZMANN = Fraction("1.380649e-23")       # J/K
ELEMENTARY_CHARGE = Fraction("1.602176634e-19")  # C

DEFAULT_ERROR_LIMIT = Fraction(1, 100)


def _fraction(value: Any, name: str) -> Q:
    """Parse an exact fraction or decimal string, rejecting binary floats."""
    if isinstance(value, bool):
        raise CentError(ErrorCode.TYPE_ERROR, f"{name}: bool is not a quantity")
    if isinstance(value, str) and "/" in value:
        try:
            return Fraction(value.strip())
        except (ValueError, ZeroDivisionError) as exc:
            raise CentError(
                ErrorCode.INVALID_INPUT,
                f"{name}: not an exact fraction: {value!r}",
            ) from exc
    try:
        return q(value, name)
    except CentError:
        raise
    except (TypeError, ValueError) as exc:  # pragma: no cover - q normalises this
        raise CentError(
            ErrorCode.TYPE_ERROR, f"{name}: expected an exact rational"
        ) from exc


def _positive(value: Any, name: str) -> Q:
    result = _fraction(value, name)
    if result <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, f"{name} must be positive")
    return result


def _json(value: Any) -> Any:
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


def _decimal(value: Q, places: int = 10) -> str:
    """Deterministic decimal truncation using integer arithmetic only."""
    sign = "-" if value < 0 else ""
    value = abs(value)
    scale = 10 ** places
    scaled = value.numerator * scale // value.denominator
    return f"{sign}{scaled // scale}.{scaled % scale:0{places}d}"


def _value_text(value: Any, places: int = 10) -> str:
    if isinstance(value, Interval):
        return f"[{_decimal(value.lo, places)}, {_decimal(value.hi, places)}]"
    if isinstance(value, Fraction):
        return _decimal(value, places)
    return str(value)


@dataclass(frozen=True)
class Quantity:
    """A declared or derived physical quantity."""

    name: str
    symbol: str
    value: Any
    unit: str
    status: str
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "symbol": self.symbol,
            "value": _json(self.value),
            "unit": self.unit,
            "status": self.status,
            "note": self.note,
        }


@dataclass(frozen=True)
class ParameterAudit:
    """One independently recomputed device quantity."""

    name: str
    symbol: str
    expected: Any
    actual: Any
    passed: bool
    rule: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "symbol": self.symbol,
            "expected": _json(self.expected),
            "actual": _json(self.actual),
            "passed": bool(self.passed),
            "rule": self.rule,
        }


@dataclass(frozen=True)
class Check:
    """A checked device relation, with the exact values that were compared."""

    name: str
    rule: str
    value: Any
    limit: Any
    passed: bool
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "rule": self.rule,
            "value": _json(self.value),
            "limit": _json(self.limit),
            "passed": bool(self.passed),
            "note": self.note,
        }


@dataclass(frozen=True)
class Pole:
    """A declared small-signal pole and the quantity that determines it."""

    name: str
    symbol: str
    time_constant: Q
    source: str
    status: str
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "symbol": self.symbol,
            "time_constant": q_to_json(self.time_constant),
            "source": self.source,
            "status": self.status,
            "note": self.note,
        }


@dataclass(frozen=True)
class ErrorTerm:
    """One conservative relative error contribution."""

    name: str
    bound: Q
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "relative_bound": q_to_json(self.bound),
            "source": self.source,
        }


@dataclass(frozen=True)
class DeviceBinding:
    """A declared physical binding for one exact route."""

    route_id: str
    name: str
    kind: str
    topology: str
    input_value: Q
    quantities: tuple[Quantity, ...]
    checks: tuple[Check, ...]
    errors: tuple[ErrorTerm, ...]
    total_error: Q
    error_limit: Q
    simulation: Mapping[str, Any]
    assumptions: tuple[str, ...]
    gaps: tuple[str, ...]
    poles: tuple[Pole, ...] = ()
    input_value_b: Q | None = None

    @property
    def passed(self) -> bool:
        return (
            all(check.passed for check in self.checks)
            and self.total_error <= self.error_limit
        )

    @property
    def parameter_audit(self) -> dict[str, Any]:
        """Recompute derived quantities independently of the binding code."""
        return audit_device_parameters(self)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "route": self.route_id,
            "kind": self.kind,
            "name": self.name,
            "status": "declared reference design; not a fabrication netlist",
            "topology": self.topology,
            "input": q_to_json(self.input_value),
            "input_b": None if self.input_value_b is None else q_to_json(self.input_value_b),
            "quantities": [item.as_dict() for item in self.quantities],
            "poles": [item.as_dict() for item in self.poles],
            "checks": [item.as_dict() for item in self.checks],
            "errors": [item.as_dict() for item in self.errors],
            "total_relative_error": q_to_json(self.total_error),
            "error_limit": q_to_json(self.error_limit),
            "passed": self.passed,
            "parameter_audit": self.parameter_audit,
            "simulation": _json(self.simulation),
            "assumptions": list(self.assumptions),
            "gaps": list(self.gaps),
        }

    def render_text(self) -> str:
        lines = [
            "=" * 78,
            "PHYSICAL DEVICE BINDING",
            "=" * 78,
            f"Route: {self.name}",
            "Status: declared reference design; not a fabrication netlist",
            "",
            "Topology",
            f"  {self.topology}",
            "",
            "Physical quantities",
        ]
        for item in self.quantities:
            lines.append(
                f"  {item.symbol:<18} {_value_text(item.value):>32} "
                f"{item.unit:<8} {item.status}"
            )
            if item.note:
                lines.append(f"      {item.note}")
        lines.append("")
        lines.append("Device-law checks")
        for item in self.checks:
            status = "pass" if item.passed else "FAIL"
            lines.append(f"  [{status:<4}] {item.name}: {item.rule}")
            lines.append(
                f"          value={_value_text(item.value)} "
                f"limit={_value_text(item.limit)}"
            )
            if item.note:
                lines.append(f"          {item.note}")
        lines.append("")
        lines.append("Declared worst-case error budget (relative)")
        for item in self.errors:
            lines.append(
                f"  {item.name:<42} {_decimal(item.bound, 10)}  ({item.source})"
            )
        lines.append("-" * 78)
        lines.append(f"  {'total':<42} {_decimal(self.total_error, 10)}")
        lines.append(f"  {'limit':<42} {_decimal(self.error_limit, 10)}")
        lines.append(f"  {'passed':<42} {self.passed}")
        lines.append("")
        lines.append("Assumptions")
        for item in self.assumptions:
            lines.append(f"  - {item}")
        lines.append("")
        lines.append("Remaining gaps")
        for item in self.gaps:
            lines.append(f"  - {item}")
        return "\n".join(lines)


def _intersection(left: Interval, right: Interval) -> Interval | None:
    lo = max(left.lo, right.lo)
    hi = min(left.hi, right.hi)
    return Interval(lo, hi) if lo <= hi else None


def _round_outward(value: Interval, places: int = 12) -> Interval:
    """Widen an enclosure to a bounded decimal rational grid.

    This keeps the exact exponential enclosure from carrying a very large
    denominator into every later quantity.  Rounding ``lo`` down and ``hi`` up
    preserves containment; the extra width is negligible against the declared
    route tolerance.
    """
    scale = 10 ** places
    lo_scaled = value.lo * scale
    hi_scaled = value.hi * scale
    lo = lo_scaled.numerator // lo_scaled.denominator
    hi = -((-hi_scaled.numerator) // hi_scaled.denominator)
    return Interval(Fraction(lo, scale), Fraction(hi, scale))


def _check(
    name: str,
    rule: str,
    value: Any,
    limit: Any,
    passed: bool,
    note: str = "",
) -> Check:
    return Check(name, rule, value, limit, bool(passed), note)


def bind_delta_sigma(
    *,
    input_value: Any = Fraction(1, 2),
    v_ref: Any = Fraction(1),
    r_in: Any = Fraction(100_000),
    c_int: Any = "1e-9",
    f_clock: Any = Fraction(10_000),
    offset_ratio: Any = Fraction(1, 200),
    samples: int = 12,
    error_limit: Any = DEFAULT_ERROR_LIMIT,
) -> DeviceBinding:
    """Bind the delta-sigma carry route to a declared RC/clock design point.

    ``R_in * C_int * f_clock = 1`` makes one clock tick equal one normalized
    integrator increment.  The error budget is static and input-referred; it
    excludes shaped quantization noise, leakage and dynamic effects.
    """
    x = _fraction(input_value, "input_value")
    v_ref_q = _positive(v_ref, "v_ref")
    r_in_q = _positive(r_in, "r_in")
    c_int_q = _positive(c_int, "c_int")
    f_clock_q = _positive(f_clock, "f_clock")
    offset_q = _fraction(offset_ratio, "offset_ratio")
    limit_q = _positive(error_limit, "error_limit")
    if not (Fraction(0) <= x <= Fraction(1)):
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            f"delta-sigma device input must be in [0, 1], got {x}",
        )
    if offset_q < 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "offset_ratio must be nonnegative")
    if int(samples) < 1:
        raise CentError(ErrorCode.DOMAIN_ERROR, "samples must be >= 1")

    route = delta_sigma_route()
    run = route.simulate(x, samples=int(samples))
    v_lsb = v_ref_q * route.quantum / route.full_scale
    v_threshold = v_lsb / 2
    rc = r_in_q * c_int_q
    rc_match = rc * f_clock_q
    v_offset = v_lsb * offset_q
    v_int_limit = v_ref_q * route.integrator_limit
    v_supply = v_int_limit + v_ref_q
    v_int_peak = v_ref_q * run.peak_integrator
    i_in_fs = v_ref_q / r_in_q

    ref_tolerance = Fraction(1, 10_000)
    rc_tolerance = Fraction(1, 10_000)
    clock_tolerance = Fraction(1, 100_000)
    rc_worst = rc_tolerance + clock_tolerance

    errors = (
        ErrorTerm("comparator offset", offset_q, "declared offset / V_lsb"),
        ErrorTerm("reference gain error", ref_tolerance, "declared V_ref tolerance"),
        ErrorTerm(
            "integrator gain error",
            rc_worst,
            "declared RC tolerance + clock tolerance",
        ),
    )
    total = sum((item.bound for item in errors), Fraction(0))
    budget_volts = total * v_lsb

    checks = (
        _check(
            "RC tick match",
            "R_in * C_int * f_clock = 1",
            rc_match,
            Fraction(1),
            rc_match == 1,
            "RC and clock define the normalized one-tick scale; finite settling is checked by cent dynamics",
        ),
        _check(
            "offset below threshold",
            "V_offset < V_threshold",
            v_offset,
            v_threshold,
            v_offset < v_threshold,
            "the declared comparator offset cannot cross the nearest threshold",
        ),
        _check(
            "RC/clock margin",
            "RC tolerance + clock tolerance <= 0.1",
            rc_worst,
            Fraction(1, 10),
            rc_worst <= Fraction(1, 10),
            "the loop gain error stays inside the declared coefficient margin",
        ),
        _check(
            "integrator excursion",
            "V_int_peak <= V_int_limit",
            v_int_peak,
            v_int_limit,
            v_int_peak <= v_int_limit,
            "the exact run's peak maps inside the declared integrator range",
        ),
        _check(
            "supply headroom",
            "V_int_limit < V_supply",
            v_int_limit,
            v_supply,
            v_int_limit < v_supply,
            "one reference-voltage headroom is reserved above the integrator limit",
        ),
        _check(
            "static error budget",
            "budget_volts <= error_limit * V_lsb",
            budget_volts,
            limit_q * v_lsb,
            budget_volts <= limit_q * v_lsb,
            "static input-referred errors stay inside the declared limit",
        ),
        _check(
            "half-LSB margin",
            "budget_volts < V_lsb / 2",
            budget_volts,
            v_lsb / 2,
            budget_volts < v_lsb / 2,
            "static errors do not consume the full decision distance",
        ),
        _check(
            "exact route run",
            "normalized route simulation passed",
            Fraction(1) if run.passed else Fraction(0),
            Fraction(1),
            run.passed,
            "the normalized exact route still meets its own tolerance",
        ),
    )

    quantities = (
        Quantity("reference voltage", "V_ref", v_ref_q, "V", "declared"),
        Quantity("input resistance", "R_in", r_in_q, "ohm", "declared"),
        Quantity("integrator capacitance", "C_int", c_int_q, "F", "declared"),
        Quantity("clock frequency", "f_clock", f_clock_q, "Hz", "declared"),
        Quantity("integrator time constant", "tau", rc, "s", "derived", "R_in * C_int"),
        Quantity("clock period", "T_clock", 1 / f_clock_q, "s", "derived", "1 / f_clock"),
        Quantity(
            "RC/clock match",
            "RC_f",
            rc_match,
            "1",
            "check",
            "unity sets the normalized scale; the finite-tick gain is checked dynamically",
        ),
        Quantity("full-scale input current", "I_in_fs", i_in_fs, "A", "derived"),
        Quantity("quantizer step", "V_lsb", v_lsb, "V", "derived"),
        Quantity("comparator threshold", "V_threshold", v_threshold, "V", "derived"),
        Quantity("comparator offset", "V_offset", v_offset, "V", "declared"),
        Quantity(
            "peak integrator excursion",
            "V_int_peak",
            v_int_peak,
            "V",
            "simulated",
            "mapped from the exact normalized run",
        ),
        Quantity("integrator range", "V_int_limit", v_int_limit, "V", "declared"),
        Quantity("positive supply", "V_supply", v_supply, "V", "derived"),
    )

    return DeviceBinding(
        route_id=route.id,
        name="First-order delta-sigma device binding",
        kind="declared-reference-design",
        topology=(
            "V_in -> error sum -> continuous-time RC integrator -> "
            "comparator at V_threshold -> clocked DFF -> feedback switch -> error sum"
        ),
        input_value=x,
        quantities=quantities,
        checks=checks,
        errors=errors,
        total_error=total,
        error_limit=limit_q,
        simulation=run.as_dict(),
        assumptions=(
            "All values are a declared reference design point, not datasheet parts, measurements or a fabrication netlist.",
            "The RC integrator is sampled once per clock; RC * f_clock = 1 sets the normalized scale, but the physical one-tick gain is 1 - exp(-T_clock/tau), checked by cent dynamics.",
            "The comparator is ideal except for the declared offset fraction; reference and passive tolerances are worst-case bounds.",
            "Quantization noise is shaped by the loop and is excluded from this static input-referred budget.",
            "Leakage, finite op-amp gain, slew, clock jitter, metastability and thermal drift are not modeled.",
        ),
        gaps=(
            "No device netlist, switch-level schematic, layout or geometry.",
            "No measured capacitor, resistor, comparator or reference data.",
            "No transient device simulation, noise spectrum or thermal model; the declared RC sampled-data transient is reported separately by cent dynamics.",
            "The error budget is a conservative sum of bounds, not a Monte Carlo distribution.",
        ),
        poles=(
            Pole(
                "Integrator pole",
                "tau",
                rc,
                "R_in * C_int",
                "derived",
                "continuous-time RC pole; the clocked sampler is modeled separately",
            ),
        ),
    )


def bind_log_domain_sqrt(
    *,
    input_value: Any = Fraction(1),
    v_ref: Any = Fraction(1),
    r_in: Any = Fraction(1_000),
    r_out: Any = Fraction(1_000_000),
    c_j: Any = "1e-11",
    c_out: Any = "1e-11",
    i_s: Any = "1e-9",
    temperature: Any = Fraction(300),
    v_out_ref: Any = Fraction(1),
    precision: int = 20,
    error_limit: Any = DEFAULT_ERROR_LIMIT,
) -> DeviceBinding:
    """Bind the log-domain square-root route to a declared diode design point.

    The nominal current path is ``I_in = V_ref*x / R_in``.  With matched
    junctions the antilog stage returns ``I_out = sqrt(I_s * I_in)`` and
    ``V_out = R_out * I_out``.  The exact squared relation
    ``V_out_ref^2 = R_out^2 * I_s * I_ref`` is checked instead of taking an
    irrational square root to choose a component value.
    """
    x = _fraction(input_value, "input_value")
    v_ref_q = _positive(v_ref, "v_ref")
    r_in_q = _positive(r_in, "r_in")
    r_out_q = _positive(r_out, "r_out")
    c_j_q = _positive(c_j, "c_j")
    c_out_q = _positive(c_out, "c_out")
    i_s_q = _positive(i_s, "i_s")
    temperature_q = _positive(temperature, "temperature")
    v_out_ref_q = _positive(v_out_ref, "v_out_ref")
    limit_q = _positive(error_limit, "error_limit")
    if not (Fraction(0) < x <= Fraction(1)):
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            f"log-domain device input must be in (0, 1], got {x}",
        )
    if isinstance(precision, bool) or not isinstance(precision, int):
        raise CentError(ErrorCode.TYPE_ERROR, "precision must be an integer")
    if not 1 <= precision <= 64:
        raise CentError(ErrorCode.DOMAIN_ERROR, "precision must be in 1..64 bits")

    route = log_domain_sqrt_route(precision=precision)
    run = route.simulate(x)
    v_t = BOLTZMANN * temperature_q / ELEMENTARY_CHARGE
    gain = Fraction(1, 2)
    i_ref = v_ref_q / r_in_q
    i_in = i_ref * x
    ln_ratio = _round_outward(log_q(i_in / i_s_q, precision))
    v_log = v_t * ln_ratio
    v_half = gain * v_log
    # ``v_half / v_t`` equals ``gain * ln_ratio`` for matched junctions;
    # using the latter avoids carrying the exact thermal-voltage denominator
    # through the exponential enclosure.
    i_out = i_s_q * (gain * ln_ratio).exp(precision)
    v_out = r_out_q * i_out
    r_d = v_t / i_in
    tau_log = r_d * c_j_q
    tau_out = r_out_q * c_out_q
    target = v_out_ref_q * sqrt_q(x, precision)
    overlap = _intersection(v_out, target)
    width_limit = v_out_ref_q * route.tolerance

    ln_fs = _round_outward(log_q(i_ref / i_s_q, precision))
    v_out_fs = r_out_q * i_s_q * (gain * ln_fs).exp(precision)
    fs_target = Interval.point(v_out_ref_q)
    fs_overlap = _intersection(v_out_fs, fs_target)
    ref_consistent = (
        v_out_ref_q * v_out_ref_q
        == r_out_q * r_out_q * i_s_q * i_ref
    )

    tol_v_ref = Fraction(1, 10_000)
    tol_r_in = Fraction(1, 10_000)
    tol_r_out = Fraction(1, 10_000)
    tol_i_s = Fraction(1, 1_000)
    gain_abs = Fraction(1, 20_000)
    temperature_gradient = Fraction(1, 10)
    ideality_mismatch = Fraction(1, 10_000)
    v_offset_log = Fraction(1, 10_000)
    v_offset_out = Fraction(1, 10_000)

    exponent_error = (
        gain_abs
        + temperature_gradient / temperature_q
        + ideality_mismatch
    )
    mismatch = exp_q(exponent_error * ln_fs.hi, precision).hi - 1

    errors = (
        ErrorTerm(
            "input resistor tolerance",
            tol_r_in / 2,
            "output scales as sqrt(1 / R_in)",
        ),
        ErrorTerm("output resistor tolerance", tol_r_out, "output scales as R_out"),
        ErrorTerm(
            "reference voltage tolerance",
            tol_v_ref / 2,
            "output scales as sqrt(V_ref)",
        ),
        ErrorTerm(
            "junction saturation mismatch",
            tol_i_s,
            "declared I_s mismatch between log and antilog junctions",
        ),
        ErrorTerm(
            "gain / temperature / ideality mismatch",
            mismatch,
            "upper bound exp(delta * ln(I_ref/I_s)) - 1",
        ),
        ErrorTerm(
            "log-stage input offset",
            v_offset_log / (v_ref_q * x) / 2,
            "declared offset referred to the input current",
        ),
        ErrorTerm(
            "output offset",
            v_offset_out / v_out_ref_q,
            "declared output-referred offset",
        ),
        ErrorTerm(
            "route enclosure tolerance",
            route.tolerance,
            "declared normalized route tolerance",
        ),
    )
    total = sum((item.bound for item in errors), Fraction(0))
    v_supply = 2 * v_out_ref_q

    checks = (
        _check(
            "reference consistency",
            "V_out_ref^2 = R_out^2 * I_s * I_ref",
            v_out_ref_q * v_out_ref_q,
            r_out_q * r_out_q * i_s_q * i_ref,
            ref_consistent,
            "checks the squared reference relation without an irrational root",
        ),
        _check(
            "normalized route",
            "exact certified-enclosure route passed",
            Fraction(1) if run.passed else Fraction(0),
            Fraction(1),
            run.passed,
            "certified route still meets its independent sqrt_q bracket",
        ),
        _check(
            "device-law output",
            "V_out enclosure overlaps V_out_ref*sqrt(x)",
            v_out.hi,
            target.lo,
            overlap is not None,
            "the declared diode law is evaluated independently of the route program",
        ),
        _check(
            "enclosure width",
            "V_out width <= V_out_ref * route tolerance",
            v_out.width,
            width_limit,
            v_out.width <= width_limit,
            "finite-precision width stays inside the declared route tolerance",
        ),
        _check(
            "full-scale output",
            "V_out(full scale) overlaps V_out_ref",
            v_out_fs.hi,
            fs_target.lo,
            fs_overlap is not None,
            "full-scale current and output resistor produce the declared reference",
        ),
        _check(
            "supply headroom",
            "V_out_high <= V_supply",
            v_out.hi,
            v_supply,
            v_out.hi <= v_supply,
            "declared two-times reference supply leaves output headroom",
        ),
        _check(
            "static error budget",
            "total_relative_error <= error_limit",
            total,
            limit_q,
            total <= limit_q,
            "conservative worst-case sum stays inside the declared accuracy limit",
        ),
        _check(
            "declared dynamic quantities",
            "C_j > 0 and C_out > 0",
            Fraction(1),
            Fraction(1),
            c_j_q > 0 and c_out_q > 0,
            "reference capacitances feed the nonlinear diode/load transient; not measured values",
        ),
    )

    quantities = (
        Quantity("reference voltage", "V_ref", v_ref_q, "V", "declared"),
        Quantity("input resistance", "R_in", r_in_q, "ohm", "declared"),
        Quantity("reference current", "I_ref", i_ref, "A", "derived"),
        Quantity("junction saturation current", "I_s", i_s_q, "A", "declared"),
        Quantity("temperature", "T", temperature_q, "K", "declared"),
        Quantity(
            "thermal voltage",
            "V_T",
            v_t,
            "V",
            "derived",
            "k_B * T / q; exact SI constants at the declared temperature",
        ),
        Quantity("junction ideality", "n", Fraction(1), "1", "declared"),
        Quantity("half-gain", "G", gain, "V/V", "declared"),
        Quantity("output resistance", "R_out", r_out_q, "ohm", "declared"),
        Quantity(
            "junction capacitance",
            "C_j",
            c_j_q,
            "F",
            "declared",
            "reference junction capacitance at the declared input",
        ),
        Quantity(
            "output load capacitance",
            "C_out",
            c_out_q,
            "F",
            "declared",
            "load plus antilog junction, reference value",
        ),
        Quantity(
            "junction small-signal resistance",
            "r_d",
            r_d,
            "ohm",
            "derived",
            "n * V_T / I_in",
        ),
        Quantity(
            "log-stage pole",
            "tau_log",
            tau_log,
            "s",
            "derived",
            "r_d * C_j",
        ),
        Quantity(
            "output pole",
            "tau_out",
            tau_out,
            "s",
            "derived",
            "R_out * C_out",
        ),
        Quantity("output reference", "V_out_ref", v_out_ref_q, "V", "declared"),
        Quantity("input voltage", "V_in", v_ref_q * x, "V", "derived"),
        Quantity("input current", "I_in", i_in, "A", "derived"),
        Quantity("log-stage voltage", "V_log", v_log, "V", "simulated"),
        Quantity("half-gain voltage", "V_half", v_half, "V", "simulated"),
        Quantity("antilog current", "I_out", i_out, "A", "simulated"),
        Quantity("bound output voltage", "V_out", v_out, "V", "simulated"),
        Quantity("target voltage", "V_target", target, "V", "check"),
        Quantity("positive supply", "V_supply", v_supply, "V", "derived"),
    )

    return DeviceBinding(
        route_id=route.id,
        name="Log-domain square-root device binding",
        kind="declared-reference-design",
        topology=(
            "V_in -> R_in -> logging junction -> unity buffer -> "
            "equal-resistor 1/2 divider -> unity buffer -> antilog junction -> "
            "R_out -> V_out"
        ),
        input_value=x,
        quantities=quantities,
        checks=checks,
        errors=errors,
        total_error=total,
        error_limit=limit_q,
        simulation=run.as_dict(),
        assumptions=(
            "All values are a declared reference design point, not datasheet parts, measurements or a fabrication netlist.",
            "Nominal log and antilog junctions share temperature, ideality and saturation current; mismatch is budgeted as a bound.",
            "Both junctions are biased in their logarithmic/exponential regions; bias networks, input bias current and loading are not modeled.",
            "The one-half stage is an ideal unity-buffered equal-resistor divider; buffer offset, gain error and bandwidth are not modeled.",
            "C_j and C_out are declared reference capacitances, not measured device values; cent dynamics integrates them through a nonlinear two-node diode/load transient at the declared input.",
            "The error budget is evaluated at the declared input and uses the worst-case log range; it is not a Monte Carlo distribution.",
            "The device-law logarithm is rounded outward to 12 decimal places before exponentiation to bound exact rational growth; containment is preserved.",
        ),
        gaps=(
            "No device netlist, bias-network synthesis, layout or geometry.",
            "No measured diode model card, thermal coupling, 1/f noise or frequency response.",
            "The declared transient uses adaptive step-doubling backward Euler and a continuous bounded-state certificate; the local coarse/fine estimate and conditional Gronwall envelope are not a formal global ODE error bound. Buffer pole, bias-network bandwidth, startup behavior and saturation recovery are absent.",
            "The error budget is a conservative sum of bounds, not a measured distribution.",
        ),
        poles=(
            Pole(
                "Log-stage pole",
                "tau_log",
                tau_log,
                "r_d * C_j",
                "derived",
                "small-signal diode resistance times junction capacitance",
            ),
            Pole(
                "Output pole",
                "tau_out",
                tau_out,
                "R_out * C_out",
                "derived",
                "declared load pole",
            ),
        ),
    )


def bind_feedback_sqrt(
    *,
    input_value: Any = Fraction(2),
    v_ref: Any = Fraction(1),
    v_supply: Any = Fraction(5),
    amplifier_gain: Any = Fraction(1_000_000),
    multiplier_gain: Any = Fraction(1),
    offset_ratio: Any = Fraction(1, 200),
    c_out: Any = "1e-11",
    r_out: Any = Fraction(1_000),
    tau_cl: Any = "1e-7",
    gain_tolerance: Any = Fraction(1, 10_000),
    multiplier_tolerance: Any = Fraction(1, 1_000),
    precision: int = 20,
    iterations: int = 64,
    error_limit: Any = DEFAULT_ERROR_LIMIT,
) -> DeviceBinding:
    """Bind the op-amp + multiplier feedback route to a declared design point.

    The normalized mapping is ``V_in = V_ref*x`` and ``V_out = V_ref*y``.
    The multiplier feedback is ``V_fb = k*V_out^2/V_ref``; the error amplifier
    drives ``V_out = A*(V_in - V_fb)``.  The finite-gain equilibrium is checked
    by evaluating that device law independently of the route solver.
    """
    x = _fraction(input_value, "input_value")
    v_ref_q = _positive(v_ref, "v_ref")
    v_supply_q = _positive(v_supply, "v_supply")
    a = _positive(amplifier_gain, "amplifier_gain")
    k = _positive(multiplier_gain, "multiplier_gain")
    offset_q = _fraction(offset_ratio, "offset_ratio")
    c_out_q = _positive(c_out, "c_out")
    r_out_q = _positive(r_out, "r_out")
    tau_cl_q = _positive(tau_cl, "tau_cl")
    tol_a = _fraction(gain_tolerance, "gain_tolerance")
    tol_k = _fraction(multiplier_tolerance, "multiplier_tolerance")
    limit_q = _positive(error_limit, "error_limit")
    if not (Fraction(0) < x <= Fraction(4)):
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            f"feedback device input must be in (0, 4], got {x}",
        )
    if offset_q < 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "offset_ratio must be nonnegative")
    if tol_a < 0 or tol_k < 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "gain tolerances must be nonnegative")
    if isinstance(precision, bool) or not isinstance(precision, int):
        raise CentError(ErrorCode.TYPE_ERROR, "precision must be an integer")
    if not 1 <= precision <= 64:
        raise CentError(ErrorCode.DOMAIN_ERROR, "precision must be in 1..64 bits")
    if isinstance(iterations, bool) or not isinstance(iterations, int):
        raise CentError(ErrorCode.TYPE_ERROR, "iterations must be an integer")
    if not 1 <= iterations <= 128:
        raise CentError(ErrorCode.DOMAIN_ERROR, "iterations must be in 1..128")

    route = opamp_multiplier_sqrt_route(
        amplifier_gain=a,
        multiplier_gain=k,
        precision=precision,
        iterations=iterations,
    )
    run = route.simulate(x)

    v_in = v_ref_q * x
    v_out = Interval(v_ref_q * run.root.lo, v_ref_q * run.root.hi)
    v_fb = (v_out.pow_int(2) * k) / v_ref_q
    v_error = Interval(v_in - v_fb.hi, v_in - v_fb.lo)
    v_drive = v_error * a
    v_target = Interval(v_ref_q * run.ideal.lo, v_ref_q * run.ideal.hi)
    v_headroom = v_ref_q / 2
    v_offset = offset_q * v_ref_q
    tau_out = r_out_q * c_out_q
    headroom_limit = v_supply_q - v_headroom

    v_fb_mid = k * v_out.midpoint * v_out.midpoint / v_ref_q
    v_drive_mid = a * (v_in - v_fb_mid)
    loop_residual = abs(v_drive_mid - v_out.midpoint)
    loop_overlap = _intersection(v_drive, v_out)
    gain_error_volts = abs(v_out.midpoint - v_target.midpoint)
    width_limit = v_ref_q * route.tolerance
    linear_limit = v_ref_q / 1000

    finite_gain_relative = run.gain_error / run.ideal.midpoint
    offset_bound = offset_q / (2 * x)
    errors = (
        ErrorTerm(
            "reference voltage gain",
            Fraction(1, 10_000),
            "output scales linearly with V_ref",
        ),
        ErrorTerm(
            "multiplier gain tolerance",
            tol_k / 2,
            "output scales as 1/sqrt(k)",
        ),
        ErrorTerm(
            "finite amplifier gain",
            finite_gain_relative,
            "finite-gain bias relative to the ideal sqrt(x/k)",
        ),
        ErrorTerm(
            "amplifier gain tolerance",
            tol_a * finite_gain_relative,
            "finite-gain bias scales with the amplifier tolerance",
        ),
        ErrorTerm(
            "amplifier input offset",
            offset_bound,
            "declared input offset / (2*x)",
        ),
        ErrorTerm(
            "multiplier feedback offset",
            offset_bound,
            "declared feedback offset / (2*x)",
        ),
        ErrorTerm(
            "route enclosure tolerance",
            route.tolerance,
            "declared normalized route tolerance",
        ),
    )
    total = sum((item.bound for item in errors), Fraction(0))

    checks = (
        _check(
            "normalized route",
            "exact finite-gain feedback route passed",
            Fraction(1) if run.passed else Fraction(0),
            Fraction(1),
            run.passed,
            "the finite-gain equilibrium meets its independent quadratic check",
        ),
        _check(
            "quadratic checker",
            "root enclosure overlaps the independent quadratic enclosure",
            Fraction(1) if run.overlap is not None else Fraction(0),
            Fraction(1),
            run.overlap is not None,
            "the route solver and the quadratic checker agree",
        ),
        _check(
            "output enclosure width",
            "V_out width <= V_ref * route tolerance",
            v_out.width,
            width_limit,
            v_out.width <= width_limit,
            "the physical output enclosure stays inside the declared tolerance",
        ),
        _check(
            "finite-gain bias",
            "|V_out - V_target| <= V_ref * route tolerance",
            gain_error_volts,
            width_limit,
            gain_error_volts <= width_limit,
            "the finite-gain bias is reported against the ideal sqrt(x/k) target",
        ),
        _check(
            "device-law loop closure",
            "V_drive overlaps V_out and |V_drive - V_out| <= V_ref * route tolerance",
            loop_residual,
            width_limit,
            loop_overlap is not None and loop_residual <= width_limit,
            "V_fb = k*V_out^2/V_ref and V_out = A*(V_in - V_fb) close independently",
        ),
        _check(
            "error-amplifier linear range",
            "max |V_error| <= V_ref / 1000",
            v_error.abs().hi,
            linear_limit,
            v_error.abs().hi <= linear_limit,
            "the small differential input keeps the error amplifier in its linear region",
        ),
        _check(
            "input headroom",
            "V_in <= V_supply - V_headroom",
            v_in,
            headroom_limit,
            v_in <= headroom_limit,
            "the declared input is below the supply headroom limit",
        ),
        _check(
            "multiplier feedback headroom",
            "V_fb_high <= V_supply - V_headroom",
            v_fb.hi,
            headroom_limit,
            v_fb.hi <= headroom_limit,
            "the multiplier output stays inside the declared supply range",
        ),
        _check(
            "output headroom",
            "V_out_high <= V_supply - V_headroom",
            v_out.hi,
            headroom_limit,
            v_out.hi <= headroom_limit,
            "the op-amp output stays inside the declared supply range",
        ),
        _check(
            "static error budget",
            "total_relative_error <= error_limit",
            total,
            limit_q,
            total <= limit_q,
            "the conservative worst-case sum stays inside the declared accuracy limit",
        ),
        _check(
            "declared dynamic quantities",
            "tau_cl > 0 and R_out * C_out > 0",
            tau_out,
            Fraction(0),
            tau_cl_q > 0 and tau_out > 0,
            "reference closed-loop and load timing feeds the nonlinear loop; not measured values",
        ),
    )

    quantities = (
        Quantity("reference voltage", "V_ref", v_ref_q, "V", "declared"),
        Quantity("input voltage", "V_in", v_in, "V", "derived", "V_ref * x"),
        Quantity("amplifier gain", "A", a, "V/V", "declared"),
        Quantity("multiplier gain", "k", k, "1", "declared"),
        Quantity(
            "multiplier feedback voltage",
            "V_fb",
            v_fb,
            "V",
            "simulated",
            "k * V_out^2 / V_ref",
        ),
        Quantity(
            "error-amplifier input",
            "V_error",
            v_error,
            "V",
            "simulated",
            "V_in - V_fb",
        ),
        Quantity(
            "error-amplifier drive",
            "V_drive",
            v_drive,
            "V",
            "simulated",
            "A * V_error",
        ),
        Quantity(
            "output voltage",
            "V_out",
            v_out,
            "V",
            "simulated",
            "V_ref * route root",
        ),
        Quantity(
            "ideal square-root target",
            "V_target",
            v_target,
            "V",
            "check",
            "V_ref * sqrt(x/k)",
        ),
        Quantity(
            "finite-gain deviation",
            "V_gain_error",
            gain_error_volts,
            "V",
            "derived",
            "|V_out - V_target|",
        ),
        Quantity(
            "device-law loop residual",
            "V_loop_residual",
            loop_residual,
            "V",
            "derived",
            "|A*(V_in - V_fb) - V_out|",
        ),
        Quantity("amplifier input offset", "V_os", v_offset, "V", "declared"),
        Quantity(
            "multiplier feedback offset",
            "V_os_mult",
            v_offset,
            "V",
            "declared",
        ),
        Quantity(
            "output load capacitance",
            "C_out",
            c_out_q,
            "F",
            "declared",
            "reference load capacitance",
        ),
        Quantity("output resistance", "R_out", r_out_q, "ohm", "declared"),
        Quantity(
            "closed-loop pole",
            "tau_cl",
            tau_cl_q,
            "s",
            "declared",
            "small-signal closed-loop reference pole",
        ),
        Quantity(
            "output load pole",
            "tau_out",
            tau_out,
            "s",
            "derived",
            "R_out * C_out",
        ),
        Quantity("positive supply", "V_supply", v_supply_q, "V", "declared"),
        Quantity(
            "supply headroom",
            "V_headroom",
            v_headroom,
            "V",
            "derived",
            "V_ref / 2",
        ),
    )

    return DeviceBinding(
        route_id=route.id,
        name="Op-amp + analog-multiplier feedback square-root device binding",
        kind="declared-reference-design",
        topology=(
            "V_in -> error amplifier (A) -> V_out drive -> "
            "analog multiplier (k * V_out^2 / V_ref) -> feedback -> error amplifier"
        ),
        input_value=x,
        quantities=quantities,
        checks=checks,
        errors=errors,
        total_error=total,
        error_limit=limit_q,
        simulation=run.as_dict(),
        assumptions=(
            "All values are a declared reference design point, not datasheet parts, measurements or a fabrication netlist.",
            "The normalized mapping is V_in = V_ref*x and V_out = V_ref*y; the multiplier feedback is V_fb = k*V_out^2/V_ref.",
            "The error amplifier is a static linear gain A; its output is checked against the declared supply and headroom, not against a saturation model.",
            "Finite amplifier gain intentionally leaves a bias below the ideal sqrt(x/k); the bias is checked and budgeted, not hidden.",
            "Offsets and gain tolerances are worst-case bounds; noise, temperature drift and multiplier nonlinearity are not modeled.",
            "tau_cl and R_out*C_out are declared reference timing quantities; the dynamic model is a slope-normalized nonlinear loop, not measured amplifier or load dynamics.",
        ),
        gaps=(
            "No device netlist, bias network, layout or geometry.",
            "No measured op-amp or multiplier model card; the AD633 /10 scaling is not modeled.",
            "The declared transient uses adaptive step-doubling backward Euler and a continuous bounded-state certificate; the local coarse/fine estimate and conditional Gronwall envelope are not a formal global ODE error bound. Slew, stability, noise, offset drift and multiplier nonlinearity beyond the declared quadratic law are absent.",
            "The error budget is a conservative sum of bounds, not a Monte Carlo or measured distribution.",
        ),
        poles=(
            Pole(
                "Closed-loop pole",
                "tau_cl",
                tau_cl_q,
                "declared small-signal closed-loop pole",
                "declared",
                "reference closed-loop timing, not a measured amplifier pole",
            ),
            Pole(
                "Output load pole",
                "tau_out",
                tau_out,
                "R_out * C_out",
                "derived",
                "declared load pole",
            ),
        ),
    )


def bind_kcl_sum(
    *,
    input_a: Any = Fraction(1, 2),
    input_b: Any = Fraction(1, 3),
    operation: str = "sum",
    error_limit: Any = DEFAULT_ERROR_LIMIT,
) -> DeviceBinding:
    """Bind the KCL route to normalized exact quantities.

    This is deliberately a normalized reference binding, not a physical
    device model.  No resistor, voltage, noise, offset or compliance values
    are declared, so the binding reports those absences as gaps instead of
    inventing an error budget.
    """
    if operation not in {"sum", "difference"}:
        raise CentError(ErrorCode.INVALID_INPUT, f"unknown KCL operation: {operation}")
    a = _fraction(input_a, "input_a")
    b = _fraction(input_b, "input_b")
    limit_q = _positive(error_limit, "error_limit")
    route = kcl_sum_route(operation=operation)
    run = route.simulate(a, b)
    expected = a + b if operation == "sum" else a - b

    checks = (
        _check(
            "normalized KCL route",
            "exact two-input route simulation passed",
            Fraction(1) if run.passed else Fraction(0),
            Fraction(1),
            run.passed,
            "the declared junction route returns its exact expected result",
        ),
        _check(
            "exact operation",
            "result = a + b" if operation == "sum" else "result = a - b",
            run.result,
            expected,
            run.result == expected,
            "no rounding or device error is introduced",
        ),
    )
    quantities = (
        Quantity("first normalized input", "a", a, "1", "declared"),
        Quantity("second normalized input", "b", b, "1", "declared"),
        Quantity(
            "normalized result",
            "total",
            run.result,
            "1",
            "simulated",
            "exact KCL sum" if operation == "sum" else "exact KCL difference",
        ),
        Quantity("expected result", "expected", expected, "1", "check"),
    )
    return DeviceBinding(
        route_id=route.id,
        name="KCL normalized sum device binding",
        kind="declared-normalized-reference",
        topology=(
            "normalized KCL junction: total = a + b"
            if operation == "sum"
            else "normalized KCL junction with exact negation: total = a - b"
        ),
        input_value=a,
        input_value_b=b,
        quantities=quantities,
        checks=checks,
        errors=(),
        total_error=Fraction(0),
        error_limit=limit_q,
        simulation=run.as_dict(),
        assumptions=(
            "The inputs and result are normalized exact rationals, not voltage or current values.",
            "The binding validates the declared KCL topology and exact operation only.",
        ),
        gaps=(
            "No physical voltage/current mapping, source/load compliance or device error model is declared.",
            "No noise, offset, finite-bandwidth, thermal or fabrication evidence is present.",
            "The zero error total is an exact normalized result, not a physical error budget.",
        ),
    )


def audit_device_parameters(binding: DeviceBinding) -> dict[str, Any]:
    """Recompute declared derived quantities from independent formulas.

    This is deliberately separate from the binding constructors: it reads only
    the public quantity table and the declared input, then checks the algebraic
    relations that should hold for the route.  A missing quantity or a mismatch
    is a visible ``gap``; no value is repaired in place.
    """
    values = {item.symbol: item.value for item in binding.quantities}
    rows: list[ParameterAudit] = []

    def add(name: str, symbol: str, expected: Any, rule: str) -> None:
        actual = values.get(symbol)
        rows.append(
            ParameterAudit(
                name=name,
                symbol=symbol,
                expected=expected,
                actual=actual,
                passed=actual is not None and actual == expected,
                rule=rule,
            )
        )

    if binding.route_id == "delta-sigma-first-order":
        v_ref = values.get("V_ref")
        r_in = values.get("R_in")
        c_int = values.get("C_int")
        f_clock = values.get("f_clock")
        v_lsb = values.get("V_lsb")
        v_int_limit = values.get("V_int_limit")
        if all(value is not None for value in (v_ref, r_in, c_int, f_clock)):
            tau = r_in * c_int
            add("integrator time constant", "tau", tau, "R_in * C_int")
            add("clock period", "T_clock", 1 / f_clock, "1 / f_clock")
            add("RC/clock match", "RC_f", tau * f_clock, "tau * f_clock")
            add("full-scale input current", "I_in_fs", v_ref / r_in, "V_ref / R_in")
        if v_lsb is not None:
            add("comparator threshold", "V_threshold", v_lsb / 2, "V_lsb / 2")
        if v_ref is not None and v_int_limit is not None:
            add("positive supply", "V_supply", v_int_limit + v_ref, "V_int_limit + V_ref")
    elif binding.route_id == "sqrt-log-domain":
        v_ref = values.get("V_ref")
        r_in = values.get("R_in")
        i_ref = values.get("I_ref")
        v_t = values.get("V_T")
        i_in = values.get("I_in")
        c_j = values.get("C_j")
        r_out = values.get("R_out")
        c_out = values.get("C_out")
        v_out_ref = values.get("V_out_ref")
        if v_ref is not None and r_in is not None:
            add("reference current", "I_ref", v_ref / r_in, "V_ref / R_in")
        if v_t is not None and i_in is not None:
            add("junction small-signal resistance", "r_d", v_t / i_in, "V_T / I_in")
        if v_t is not None and i_in is not None and c_j is not None:
            add("log-stage pole", "tau_log", (v_t / i_in) * c_j, "(V_T / I_in) * C_j")
        if r_out is not None and c_out is not None:
            add("output pole", "tau_out", r_out * c_out, "R_out * C_out")
        if v_ref is not None:
            add("input voltage", "V_in", v_ref * binding.input_value, "V_ref * input")
        if i_ref is not None:
            add("input current", "I_in", i_ref * binding.input_value, "I_ref * input")
        if v_out_ref is not None:
            add("positive supply", "V_supply", 2 * v_out_ref, "2 * V_out_ref")
    elif binding.route_id == "sum-kcl":
        a = values.get("a")
        b = values.get("b")
        operation = (binding.simulation or {}).get("operation")
        if a is not None and b is not None and operation in {"sum", "difference"}:
            expected = a + b if operation == "sum" else a - b
            add("normalized result", "total", expected, "a + b" if operation == "sum" else "a - b")
    elif binding.route_id == "sqrt-opamp-multiplier":
        v_ref = values.get("V_ref")
        r_out = values.get("R_out")
        c_out = values.get("C_out")
        if v_ref is not None:
            add("input voltage", "V_in", v_ref * binding.input_value, "V_ref * input")
            add("supply headroom", "V_headroom", v_ref / 2, "V_ref / 2")
        if r_out is not None and c_out is not None:
            add("output load pole", "tau_out", r_out * c_out, "R_out * C_out")

    failures = [row.symbol for row in rows if not row.passed]
    return {
        "status": "pass" if rows and not failures else "gap",
        "checked": len(rows),
        "failures": failures,
        "rows": [row.as_dict() for row in rows],
        "detail": (
            f"{len(rows)} derived quantity relation(s) independently recomputed"
            if rows and not failures
            else "derived quantity audit failed: " + ", ".join(failures or ["no rows"])
        ),
    }


__all__ = [
    "BOLTZMANN",
    "DEFAULT_ERROR_LIMIT",
    "DeviceBinding",
    "ELEMENTARY_CHARGE",
    "ErrorTerm",
    "ParameterAudit",
    "Pole",
    "Quantity",
    "SCHEMA",
    "audit_device_parameters",
    "bind_delta_sigma",
    "bind_feedback_sqrt",
    "bind_kcl_sum",
    "bind_log_domain_sqrt",
]
