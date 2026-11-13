"""Exact tick evaluator for ¢ programs (CentCalculus2 §7–§8).

Every numeric wire carries a :class:`fractions.Fraction`; transcendental
primitives return a certified :class:`~cent_compiler.interval.Interval` never a
float; conservative primitives carry a
:class:`~cent_compiler.port.PhysicalPort`.  Nothing in this module uses binary
floating point.

State discipline
----------------
Each stateful *instruction whose output wire is read on that wire's own name*
owns a slot keyed by its output wire, so two ``rate`` nodes in one program do
not share history.  A tick builds a fresh
:class:`~cent_compiler.state.EvalContext`; slots are written only on success and
the committed state is installed only after every instruction has produced a
value.  A raised :class:`CentError` therefore leaves the machine exactly as it
was.

Feedback
--------
An input wire produced later in the schedule is a back edge and reads the
previous tick's value.  On the very first tick that value is the producer's
documented initial value (``_initial_output``), which only exists for stateful
primitives — the static checker already rejected every other cycle.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Callable, Iterable, Mapping, Sequence

from .exact import (
    CentError,
    ErrorCode,
    Q,
    clamp,
    div as exact_div,
    q,
    wrap_periodic,
)
from .geometry import (
    BoundaryCondition,
    GridDomain,
    ScalarField,
    TwoForm,
    VectorField,
    curl_2form_at,
    divergence_at,
    gradient,
    laplacian_at,
)
from .interval import Interval, as_interval, exp_q, log_q, sqrt_q
from .port import (
    Gyrator,
    PhysicalPort,
    Transformer,
    dissipator,
    ideal_transducer,
    junction_0,
    junction_1,
    kinetic_store,
    potential_store,
)
from .program import (
    Analysis,
    Instruction,
    Program,
    analyse,
    coerce_input,
    kind_of,
    require_kind,
)
from .state import EvalContext, MachineState, SplitMix64
from .vocabulary import STATEFUL_OPS, canonical_op

_DEFAULT_PREC = 64


# ---------------------------------------------------------------------------
# coercion helpers
# ---------------------------------------------------------------------------

def _num(x: Any, op: str) -> Q:
    """Coerce an exact numeric wire; intervals are a type error here."""
    if isinstance(x, Fraction):
        return x
    if isinstance(x, int) and not isinstance(x, bool):
        return q(x)
    raise CentError(
        ErrorCode.TYPE_ERROR,
        f"{op}: expected an exact rational, got {type(x).__name__}",
    )


def _is_interval(x: Any) -> bool:
    return isinstance(x, Interval)


def _add(a: Any, b: Any) -> Any:
    if _is_interval(a) or _is_interval(b):
        return as_interval(a) + as_interval(b)
    return _num(a, "sum") + _num(b, "sum")


def _sub(a: Any, b: Any) -> Any:
    if _is_interval(a) or _is_interval(b):
        return as_interval(a) - as_interval(b)
    return _num(a, "sub") - _num(b, "sub")


def _mul(a: Any, b: Any) -> Any:
    if _is_interval(a) or _is_interval(b):
        return as_interval(a) * as_interval(b)
    return _num(a, "mult") * _num(b, "mult")


def _div_values(a: Any, b: Any) -> Any:
    if _is_interval(a) or _is_interval(b):
        return as_interval(a) / as_interval(b)
    return exact_div(_num(a, "div"), _num(b, "div"))


def _zero_like(x: Any) -> Any:
    return Interval.point(Fraction(0)) if _is_interval(x) else Fraction(0)


def _field(x: Any, op: str) -> ScalarField:
    if not isinstance(x, ScalarField):
        raise CentError(ErrorCode.TYPE_ERROR, f"{op}: expected a scalar field")
    return x


def _vector_field(x: Any, op: str) -> VectorField:
    if not isinstance(x, VectorField):
        raise CentError(ErrorCode.TYPE_ERROR, f"{op}: expected a vector field")
    return x


def _port(x: Any, op: str) -> PhysicalPort:
    if not isinstance(x, PhysicalPort):
        raise CentError(ErrorCode.TYPE_ERROR, f"{op}: expected a physical port")
    return x


def _precision(params: Mapping[str, Any]) -> int:
    return int(params.get("precision", _DEFAULT_PREC))


def _index(params: Mapping[str, Any], ndim: int, op: str) -> tuple[int, ...]:
    raw = params.get("index")
    if raw is None:
        raise CentError(ErrorCode.VALIDATION_ERROR, f"{op}: parameter 'index' is required")
    idx = tuple(int(i) for i in raw)
    if len(idx) != ndim:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            f"{op}: index has {len(idx)} coordinates, expected {ndim}",
        )
    return idx


# ---------------------------------------------------------------------------
# exact rational powers (needed by ¢_translinear)
# ---------------------------------------------------------------------------

def _int_root(n: int, k: int) -> int | None:
    """Exact ``k``-th root of a nonnegative integer, or ``None``."""
    if n < 0:
        return None
    if n in (0, 1):
        return n
    lo, hi = 1, 1
    while pow(hi, k) <= n:
        hi *= 2
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if pow(mid, k) <= n:
            lo = mid
        else:
            hi = mid - 1
    return lo if pow(lo, k) == n else None


def _exact_nth_root(x: Q, k: int) -> Q | None:
    rn, rd = _int_root(x.numerator, k), _int_root(x.denominator, k)
    if rn is None or rd is None:
        return None
    return Fraction(rn, rd)


def _pow_rational(base: Q, exponent: Q, precision: int = _DEFAULT_PREC) -> Any:
    """``base ** exponent`` exactly when possible, otherwise a certified interval."""
    if exponent.denominator == 1:
        n = exponent.numerator
        if n == 0:
            return Fraction(1)
        if n > 0:
            return base ** n
        if base == 0:
            raise CentError(ErrorCode.DIVISION_BY_ZERO, "zero raised to a negative power")
        return Fraction(1) / (base ** (-n))
    if base < 0:
        raise CentError(
            ErrorCode.DOMAIN_ERROR, "a fractional power of a negative rational is not real"
        )
    if base == 0:
        if exponent > 0:
            return Interval.point(Fraction(0))
        raise CentError(ErrorCode.DOMAIN_ERROR, "zero raised to a nonpositive power")
    root = _exact_nth_root(base, exponent.denominator)
    if root is not None:
        return _pow_rational(root, Fraction(exponent.numerator), precision)
    return exp_q(exponent * log_q(base, precision), precision)


# ---------------------------------------------------------------------------
# matrix helpers (¢_state_space)
# ---------------------------------------------------------------------------

def _matrix(value: Any, name: str) -> list[list[Q]]:
    try:
        rows = [[q(v) for v in row] for row in value]
    except TypeError as exc:
        raise CentError(ErrorCode.INVALID_INPUT, f"{name}: expected a nested sequence") from exc
    if not rows or not rows[0]:
        raise CentError(ErrorCode.INVALID_INPUT, f"{name}: matrix is empty")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise CentError(ErrorCode.INVALID_INPUT, f"{name}: ragged matrix")
    return rows


def _matvec(matrix: Sequence[Sequence[Q]], vector: Sequence[Q], name: str) -> list[Q]:
    if any(len(row) != len(vector) for row in matrix):
        raise CentError(
            ErrorCode.INVALID_INPUT,
            f"{name}: {len(matrix)}x{len(matrix[0])} matrix does not fit a {len(vector)}-vector",
        )
    return [sum((a * b for a, b in zip(row, vector)), Fraction(0)) for row in matrix]


def _vector(value: Any, name: str) -> list[Q]:
    try:
        return [q(v) for v in value]
    except TypeError as exc:
        raise CentError(ErrorCode.INVALID_INPUT, f"{name}: expected a sequence") from exc


# ---------------------------------------------------------------------------
# handlers
# ---------------------------------------------------------------------------
# Every handler receives (args, params, ctx, key, tick).
# ---------------------------------------------------------------------------

def _h_sum(args, p, ctx, key, tick):
    total = args[0]
    for value in args[1:]:
        total = _add(total, value)
    return total


def _h_neg(args, p, ctx, key, tick):
    return -args[0]


def _h_mult(args, p, ctx, key, tick):
    total = args[0]
    for value in args[1:]:
        total = _mul(total, value)
    return total


def _h_scale(args, p, ctx, key, tick):
    factor = q(p["factor"])
    x = args[0]
    return as_interval(x).scale(factor) if _is_interval(x) else _num(x, "scale") * factor


def _h_accum(args, p, ctx, key, tick):
    running = ctx.read_slot(key).get("value", Fraction(0))
    new = _add(running, args[0])
    ctx.write_slot(key, {"value": new})
    return new


def _h_rate(args, p, ctx, key, tick):
    dt = q(p["dt"])
    if dt <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "rate: dt must be strictly positive")
    x = args[0]
    prev = ctx.read_slot(key).get("prev")
    ctx.write_slot(key, {"prev": x})
    if prev is None:
        return _zero_like(x)
    return _div_values(_sub(x, prev), dt)


def _h_wrap(args, p, ctx, key, tick):
    return wrap_periodic(_num(args[0], "wrap"), q(p["period"]))


def _h_spatial(args, p, ctx, key, tick):
    field = _field(args[0], "spatial")
    index = p.get("index")
    idx = tuple(int(i) for i in index) if index is not None else tuple(0 for _ in range(field.ndim))
    return field.at(idx)


def _h_exp(args, p, ctx, key, tick):
    precision = _precision(p)
    x = args[0]
    return as_interval(x).exp(precision) if _is_interval(x) else exp_q(_num(x, "exp"), precision)


def _h_log(args, p, ctx, key, tick):
    precision = _precision(p)
    x = args[0]
    if _is_interval(x):
        return x.log(precision)
    return log_q(_num(x, "log"), precision)


def _h_sat(args, p, ctx, key, tick):
    return clamp(_num(args[0], "sat"), q(p["lo"]), q(p["hi"]))


def _h_hysteresis(args, p, ctx, key, tick):
    lower, upper = q(p["lower"]), q(p["upper"])
    if lower >= upper:
        raise CentError(ErrorCode.DOMAIN_ERROR, "hysteresis: lower must be below upper")
    x = _num(args[0], "hysteresis")
    current = bool(ctx.read_slot(key).get("bit", bool(p.get("initial", False))))
    if x >= upper:
        current = True
    elif x <= lower:
        current = False
    ctx.write_slot(key, {"bit": current})
    return 1 if current else 0


def _h_delay(args, p, ctx, key, tick):
    ticks = int(p["ticks"])
    if ticks < 1:
        raise CentError(ErrorCode.DOMAIN_ERROR, "delay: ticks must be >= 1")
    initial = q(p.get("initial", 0))
    buf = list(ctx.read_slot(key).get("buf", []))
    if len(buf) >= ticks:
        out = buf[0]
        buf = buf[1:]
    else:
        out = initial
    buf.append(args[0])
    ctx.write_slot(key, {"buf": buf})
    return out


def _h_grad(args, p, ctx, key, tick):
    return gradient(_field(args[0], "grad"), q(p.get("h", 1)))


def _h_div_spatial(args, p, ctx, key, tick):
    vector = _vector_field(args[0], "div_spatial")
    idx = _index(p, vector.ndim, "div_spatial")
    return divergence_at(vector, idx, q(p.get("h", 1)))


def _h_curl(args, p, ctx, key, tick):
    vector = _vector_field(args[0], "curl")
    idx = _index(p, vector.ndim, "curl")
    return curl_2form_at(vector, idx, q(p.get("h", 1)))


def _h_laplacian(args, p, ctx, key, tick):
    field = _field(args[0], "laplacian")
    idx = _index(p, field.ndim, "laplacian")
    axes = p.get("axes")
    return laplacian_at(field, idx, q(p.get("h", 1)), tuple(axes) if axes is not None else None)


def _sample_with_bc(field: ScalarField, domain: GridDomain, index: tuple[int, ...]) -> Q:
    if domain.in_bounds(index):
        return field.at(index)
    for axis, (i, n) in enumerate(zip(index, domain.shape)):
        if i < 0 or i >= n:
            gap = -i if i < 0 else i - (n - 1)
            inner = list(index)
            inner[axis] = 0 if i < 0 else n - 1
            interior = _sample_with_bc(field, domain, tuple(inner))
            return domain.boundary.extrapolate(interior, domain.spacing, gap)
    raise AssertionError("unreachable")  # pragma: no cover


def _h_boundary(args, p, ctx, key, tick):
    field = _field(args[0], "boundary")
    domain = GridDomain(
        tuple(int(s) for s in p["shape"]),
        q(p.get("spacing", 1)),
        BoundaryCondition(
            kind=str(p.get("kind", "dirichlet")),
            value=p.get("value", 0),
            alpha=p.get("alpha", 1),
            beta=p.get("beta", 1),
            gamma=p.get("gamma", 0),
        ),
    )
    if domain.ndim != field.ndim:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            f"boundary: domain has {domain.ndim} axes, field has {field.ndim}",
        )
    return ScalarField(
        lambda idx: _sample_with_bc(field, domain, tuple(int(i) for i in idx)),
        field.ndim,
        f"boundary({field.name})",
    )


def _h_junction_0(args, p, ctx, key, tick):
    ports = [_port(a, "junction_0") for a in args]
    return junction_0(ports, p.get("resolved"))[-1 if p.get("resolved") is None else int(p["resolved"])]


def _h_junction_1(args, p, ctx, key, tick):
    ports = [_port(a, "junction_1") for a in args]
    return junction_1(ports, p.get("resolved"))[-1 if p.get("resolved") is None else int(p["resolved"])]


def _h_gyrator(args, p, ctx, key, tick):
    return Gyrator(q(p["resistance"])).apply(_port(args[0], "gyrator"))


def _h_transformer(args, p, ctx, key, tick):
    return Transformer(q(p["ratio"])).apply(_port(args[0], "transformer"))


def _h_dissipate(args, p, ctx, key, tick):
    port, entropy_rate = dissipator(q(p["resistance"]), _num(args[0], "dissipate"),
                                   q(p["temperature"]))
    ctx.write_slot(key, {"entropy_rate": entropy_rate})
    return port


def _h_store_pot(args, p, ctx, key, tick):
    capacitance, dt = q(p["capacitance"]), q(p["dt"])
    flow = _num(args[0], "store_pot")
    charge = ctx.read_slot(key).get("charge", Fraction(0)) + flow * dt
    ctx.write_slot(key, {"charge": charge})
    return potential_store(capacitance, charge, flow)[0]


def _h_store_kin(args, p, ctx, key, tick):
    inductance, dt = q(p["inductance"]), q(p["dt"])
    effort = _num(args[0], "store_kin")
    flux = ctx.read_slot(key).get("flux", Fraction(0)) + effort * dt
    ctx.write_slot(key, {"flux": flux})
    return kinetic_store(inductance, flux, effort)[0]


def _h_transduce(args, p, ctx, key, tick):
    port, loss = ideal_transducer(q(p["ratio"]), _port(args[0], "transduce"),
                                 q(p.get("efficiency", 1)))
    ctx.write_slot(key, {"loss": loss})
    return port


def _h_noise(args, p, ctx, key, tick):
    amplitude = q(p["amplitude"])
    if amplitude < 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "noise: amplitude must be nonnegative")
    slot = ctx.read_slot(key)
    if "state" in slot:
        rng = SplitMix64(slot["state"])
    else:
        rng = SplitMix64(int(p.get("seed", ctx.state.seed)))
    sign = rng.sign()
    ctx.write_slot(key, {"state": rng.state})
    return amplitude if sign > 0 else -amplitude


def _h_quantize(args, p, ctx, key, tick):
    quantum = q(p["quantum"])
    if quantum <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "quantize: quantum must be positive")
    x = _num(args[0], "quantize")
    magnitude = abs(x) / quantum
    # Ties away from zero: floor(|x|/q + 1/2) rounds .5 up in magnitude.
    steps = (magnitude + Fraction(1, 2)).__floor__()
    return Fraction(steps) * quantum * (1 if x >= 0 else -1)


def _h_entropy(args, p, ctx, key, tick):
    port = _port(args[0], "entropy")
    temperature = q(p["temperature"])
    if temperature <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "entropy: temperature must be positive")
    if port.power < 0:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            "entropy: an active port creates power, so it has no entropy production",
        )
    return port.power / temperature


def _h_recip(args, p, ctx, key, tick):
    x = args[0]
    return as_interval(x).reciprocal() if _is_interval(x) else exact_div(Fraction(1), _num(x, "recip"))


def _h_div(args, p, ctx, key, tick):
    return _div_values(args[0], args[1])


def _h_sqrt(args, p, ctx, key, tick):
    precision = _precision(p)
    x = args[0]
    return x.sqrt(precision) if _is_interval(x) else sqrt_q(_num(x, "sqrt"), precision)


def _h_eq(args, p, ctx, key, tick):
    a, b = args
    if _is_interval(a) or _is_interval(b):
        ia, ib = as_interval(a), as_interval(b)
        return 1 if (ia.is_point and ib.is_point and ia.lo == ib.lo) else 0
    return 1 if _num(a, "eq") == _num(b, "eq") else 0


def _h_translinear(args, p, ctx, key, tick):
    exponents = [q(e) for e in p["exponents"]]
    if len(exponents) != len(args):
        raise CentError(
            ErrorCode.VALIDATION_ERROR,
            f"translinear: {len(exponents)} exponent(s) for {len(args)} input(s)",
        )
    precision = _precision(p)
    total: Any = Fraction(1)
    for value, exponent in zip(args, exponents):
        total = _mul(total, _pow_rational(_num(value, "translinear"), exponent, precision))
    return total


def _h_state_space(args, p, ctx, key, tick):
    a = _matrix(p["A"], "A")
    b = _matrix(p["B"], "B")
    c = _matrix(p["C"], "C")
    d = _matrix(p["D"], "D")
    u = _vector(args[0], "state_space input")
    n = len(a[0])
    if len(a) != len(c[0]):
        raise CentError(ErrorCode.INVALID_INPUT, "A rows must match C columns")
    if len(b) != len(a):
        raise CentError(ErrorCode.INVALID_INPUT, "B rows must match A rows")
    if len(c) != len(d) or len(d[0]) != len(b[0]):
        raise CentError(ErrorCode.INVALID_INPUT, "C and D shapes must agree with B")
    if len(u) != len(b[0]):
        raise CentError(ErrorCode.INVALID_INPUT, "control vector does not match B columns")
    slot = ctx.read_slot(key)
    x = [q(v) for v in slot.get("x", [Fraction(0)] * n)]
    if len(x) != n:
        raise CentError(ErrorCode.INVALID_INPUT, "stored state vector has the wrong length")
    y = [sum((c[i][j] * x[j] for j in range(n)), Fraction(0))
         + sum((d[i][j] * u[j] for j in range(len(u))), Fraction(0))
         for i in range(len(c))]
    ax = _matvec(a, x, "A")
    bu = _matvec(b, u, "B")
    ctx.write_slot(key, {"x": [ax[i] + bu[i] for i in range(n)]})
    return tuple(y)


def _h_pid(args, p, ctx, key, tick):
    kp, ki, kd, dt = q(p["kp"]), q(p["ki"]), q(p["kd"]), q(p["dt"])
    if dt <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "pid: dt must be strictly positive")
    error = _num(args[0], "pid")
    slot = ctx.read_slot(key)
    integral = q(slot.get("integral", p.get("initial", 0)))
    previous = slot.get("previous")
    integral = integral + error * dt
    derivative = Fraction(0) if previous is None else (error - q(previous)) / dt
    ctx.write_slot(key, {"integral": integral, "previous": error})
    return kp * error + ki * integral + kd * derivative


def _h_phase_locked_loop(args, p, ctx, key, tick):
    center, gain, dt = q(p["center_frequency"]), q(p["gain"]), q(p["dt"])
    if dt <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "phase_locked_loop: dt must be positive")
    error = _num(args[0], "phase_locked_loop")
    phase = q(ctx.read_slot(key).get("phase", p.get("initial_phase", 0)))
    phase = phase + (center + gain * error) * dt
    ctx.write_slot(key, {"phase": phase})
    return phase


def _h_transmission_line(args, p, ctx, key, tick):
    segments = int(p["segments"])
    if segments < 1:
        raise CentError(ErrorCode.DOMAIN_ERROR, "transmission_line: segments must be >= 1")
    reflection = q(p.get("reflection", 0))
    if not (-1 <= reflection <= 1):
        raise CentError(ErrorCode.DOMAIN_ERROR, "transmission_line: |reflection| must be <= 1")
    x = _num(args[0], "transmission_line")
    slot = ctx.read_slot(key)
    cells = [q(v) for v in slot.get("cells", [q(p.get("initial", 0))] * segments)]
    out = cells[0]
    incoming = x + reflection * out
    ctx.write_slot(key, {"cells": cells[1:] + [incoming]})
    return out


def _h_kalman_observer(args, p, ctx, key, tick):
    process = q(p["process_variance"])
    measurement = q(p["measurement_variance"])
    if process < 0 or measurement <= 0:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            "kalman_observer: process variance >= 0 and measurement variance > 0",
        )
    z = _num(args[0], "kalman_observer")
    slot = ctx.read_slot(key)
    x = q(slot.get("x", p.get("initial_x", 0)))
    covariance = q(slot.get("p", p.get("initial_p", 1)))
    covariance = covariance + process
    gain = covariance / (covariance + measurement)
    x = x + gain * (z - x)
    covariance = (1 - gain) * covariance
    ctx.write_slot(key, {"x": x, "p": covariance})
    return x


def _h_thermo_electric(args, p, ctx, key, tick):
    port = _port(args[0], "thermo_electric")
    seebeck, resistance, temperature = q(p["seebeck"]), q(p["resistance"]), q(p["temperature"])
    if temperature <= 0 or resistance <= 0:
        raise CentError(
            ErrorCode.DOMAIN_ERROR, "thermo_electric: T > 0 and R > 0 are required"
        )
    current = port.flow
    heat = seebeck * temperature * current + current * current * resistance
    return PhysicalPort(temperature, heat / temperature)


def _h_delta_sigma_modulator(args, p, ctx, key, tick):
    order = int(p.get("order", 1))
    if order not in (1, 2):
        raise CentError(ErrorCode.DOMAIN_ERROR, "delta_sigma_modulator: order must be 1 or 2")
    threshold = q(p["threshold"])
    if threshold <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "delta_sigma_modulator: threshold must be > 0")
    x = _num(args[0], "delta_sigma_modulator")
    slot = ctx.read_slot(key)
    i1 = q(slot.get("i1", 0))
    i2 = q(slot.get("i2", 0))
    last = int(slot.get("last", 0))
    i1 = i1 + x - last
    if order == 1:
        bit = 1 if i1 >= threshold else 0
        ctx.write_slot(key, {"i1": i1, "i2": Fraction(0), "last": bit})
        return bit
    i2 = i2 + i1 - last
    bit = 1 if i2 >= threshold else 0
    ctx.write_slot(key, {"i1": i1, "i2": i2, "last": bit})
    return bit


HANDLERS: dict[str, Callable[..., Any]] = {
    "sum": _h_sum,
    "neg": _h_neg,
    "mult": _h_mult,
    "scale": _h_scale,
    "accum": _h_accum,
    "rate": _h_rate,
    "wrap": _h_wrap,
    "spatial": _h_spatial,
    "exp": _h_exp,
    "log": _h_log,
    "sat": _h_sat,
    "hysteresis": _h_hysteresis,
    "delay": _h_delay,
    "grad": _h_grad,
    "div_spatial": _h_div_spatial,
    "curl": _h_curl,
    "laplacian": _h_laplacian,
    "boundary": _h_boundary,
    "junction_0": _h_junction_0,
    "junction_1": _h_junction_1,
    "gyrator": _h_gyrator,
    "transformer": _h_transformer,
    "dissipate": _h_dissipate,
    "store_pot": _h_store_pot,
    "store_kin": _h_store_kin,
    "transduce": _h_transduce,
    "noise": _h_noise,
    "quantize": _h_quantize,
    "entropy": _h_entropy,
    "recip": _h_recip,
    "div": _h_div,
    "sqrt": _h_sqrt,
    "eq": _h_eq,
    "translinear": _h_translinear,
    "state_space": _h_state_space,
    "pid": _h_pid,
    "phase_locked_loop": _h_phase_locked_loop,
    "transmission_line": _h_transmission_line,
    "kalman_observer": _h_kalman_observer,
    "thermo_electric": _h_thermo_electric,
    "delta_sigma_modulator": _h_delta_sigma_modulator,
}


def _initial_output(instr: Instruction, tick: int = 0) -> Any:
    """Documented previous-tick value of a stateful producer (first tick only)."""
    p = instr.params
    op = instr.op
    if op == "delay":
        return q(p.get("initial", 0))
    if op == "hysteresis":
        return 1 if p.get("initial", False) else 0
    if op == "phase_locked_loop":
        return q(p.get("initial_phase", 0))
    if op == "transmission_line":
        return q(p.get("initial", 0))
    if op == "kalman_observer":
        return q(p.get("initial_x", 0))
    if op == "store_pot" or op == "store_kin":
        return PhysicalPort(Fraction(0), Fraction(0))
    if op == "rate" or op == "accum" or op == "noise":
        return Fraction(0)
    if op == "pid":
        return q(p.get("initial", 0))
    if op == "delta_sigma_modulator":
        return 0
    raise CentError(
        ErrorCode.CYCLE_DETECTED,
        f"back edge from {op!r} has no documented initial value",
        where=instr.out,
    )


def apply(
    op: str,
    args: Sequence[Any],
    params: Mapping[str, Any],
    ctx: EvalContext,
    key: str,
    tick: int,
) -> Any:
    """Dispatch one instruction."""
    name = canonical_op(op)
    handler = HANDLERS.get(name)
    if handler is None:
        raise CentError(ErrorCode.UNSUPPORTED, f"no evaluator for ¢ primitive {name!r}", where=key)
    return handler(tuple(args), params, ctx, key, tick)


# ---------------------------------------------------------------------------
# evaluator
# ---------------------------------------------------------------------------

class Evaluator:
    """Executes a :class:`~cent_compiler.program.Program` exactly, tick by tick."""

    def __init__(
        self,
        program: Program,
        *,
        state: MachineState | None = None,
        seed: int = 0,
        analysis: Analysis | None = None,
    ):
        self.program = program
        self.analysis = analysis or analyse(program)
        self.state = state if state is not None else MachineState(seed=int(seed))

    # -- one tick ---------------------------------------------------------
    def tick(self, inputs: Mapping[str, Any]) -> dict[str, Any]:
        program, analysis, state = self.program, self.analysis, self.state
        previous: dict[str, Any] = dict(state.slot("__wires__"))
        producers = {instr.out: idx for idx, instr in enumerate(program.instructions)}
        ctx = EvalContext(state=state)

        values: dict[str, Any] = {}
        for wire, kind in program.inputs.items():
            if wire in inputs:
                values[wire] = coerce_input(inputs[wire], kind, wire)
            elif wire in previous:
                values[wire] = coerce_input(previous[wire], kind, wire)
            else:
                raise CentError(
                    ErrorCode.INVALID_INPUT,
                    f"tick {state.clock}: no value for program input {wire!r}",
                )
            require_kind(values[wire], kind, wire)

        for idx in analysis.order:
            instr = program.instructions[idx]
            back = analysis.back_edges.get(idx, frozenset())
            args = []
            for wire in instr.inputs:
                if wire in back:
                    if wire in previous:
                        args.append(previous[wire])
                    else:
                        producer = producers.get(wire)
                        if producer is None:
                            raise CentError(
                                ErrorCode.VALIDATION_ERROR,
                                f"back edge from unknown wire {wire!r}",
                                where=instr.out,
                            )
                        args.append(_initial_output(program.instructions[producer], state.clock))
                else:
                    args.append(values[wire])
            result = apply(instr.op, args, instr.params, ctx, instr.out, state.clock)
            require_kind(result, analysis.kinds[instr.out], instr.out)
            values[instr.out] = result

        ctx.write_slot("__wires__", dict(values))
        self.state = ctx.next_clock(state)
        return {name: values[wire] for name, wire in program.outputs.items()}

    # -- many ticks -------------------------------------------------------
    def run(
        self,
        feed: Iterable[Mapping[str, Any]] | Callable[[int], Mapping[str, Any]],
        ticks: int | None = None,
    ) -> tuple[dict[str, Any], ...]:
        if callable(feed):
            if ticks is None:
                raise CentError(
                    ErrorCode.INVALID_INPUT, "a callable feed needs an explicit tick count"
                )
            sequence = [feed(i) for i in range(int(ticks))]
        else:
            sequence = list(feed)
            if ticks is not None:
                sequence = sequence[: int(ticks)]
        return tuple(self.tick(item) for item in sequence)

    # -- introspection ----------------------------------------------------
    @property
    def clock(self) -> int:
        return self.state.clock


def run_program(
    program: Program,
    feed: Iterable[Mapping[str, Any]] | Callable[[int], Mapping[str, Any]],
    ticks: int | None = None,
    *,
    seed: int = 0,
) -> tuple[dict[str, Any], ...]:
    """Convenience wrapper: analyse once, then run every tick."""
    return Evaluator(program, seed=seed).run(feed, ticks)
